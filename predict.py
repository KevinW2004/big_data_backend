import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl
from dgl.nn.pytorch import GraphConv
from sklearn.metrics import f1_score


# 数据加载函数
def load_new_data(device):
    # 读取数据
    papers = pd.read_csv('./dataset/papers.csv')
    features = pd.read_csv('./dataset/node-feat.csv', header=None).values.astype(np.float32)
    edges = pd.read_csv('./dataset/edge.csv', header=None).values.T.astype(np.int32)

    # 提取边信息
    src, dst = edges[0], edges[1]

    # 构建图
    graph = dgl.graph((src, dst), num_nodes=len(features))
    graph = dgl.to_bidirected(graph)
    graph = dgl.add_self_loop(graph).to(device)

    # 处理标签和年份
    papers['category'] = papers['category'].replace('Unknown', -1)  # 将 Unknown 替换为占位符
    papers['category'] = papers['category'].astype('category').cat.codes
    labels = papers['category'].values
    years = papers['year'].values

    # 按年份划分数据集
    train_mask = (years <= 2017)
    val_mask = (years == 2018)
    test_mask = (years >= 2019)

    # 转换为 Tensor
    features = torch.tensor(features, dtype=torch.float32).to(device)
    labels = torch.tensor(labels, dtype=torch.long).to(device)
    train_mask = torch.tensor(train_mask, dtype=torch.bool).to(device)
    val_mask = torch.tensor(val_mask, dtype=torch.bool).to(device)
    test_mask = torch.tensor(test_mask, dtype=torch.bool).to(device)

    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
    print(
        f"Train size: {train_mask.sum().item()}, Val size: {val_mask.sum().item()}, Test size: {test_mask.sum().item()}")
    return graph, features, labels, train_mask, val_mask, test_mask, papers


# 模型定义与训练代码复用
class GCN(nn.Module):
    def __init__(self, input_dim, hidden_sizes, num_classes):
        super(GCN, self).__init__()
        layers = []
        layers.append(GraphConv(input_dim, hidden_sizes[0], activation=F.relu))
        for i in range(1, len(hidden_sizes)):
            layers.append(GraphConv(hidden_sizes[i - 1], hidden_sizes[i], activation=F.relu))
        layers.append(GraphConv(hidden_sizes[-1], num_classes))
        self.layers = nn.ModuleList(layers)

    def forward(self, g, features):
        h = features
        for i in range(len(self.layers) - 1):
            h = self.layers[i](g, h)
        h = self.layers[-1](g, h)
        return h


def evaluate(model, g, features, labels, mask):
    model.eval()
    with torch.no_grad():
        logits = model(g, features)
        logits = logits[mask]
        labels = labels[mask]
        score, indices = torch.max(logits, dim=1)
        correct = torch.sum(indices == labels)
        acc = correct.item() / len(labels)
        f1 = f1_score(labels.cpu(), indices.cpu(), average='macro')
        return acc, f1


def train_model(model_class, model_name, graph, features, labels, train_mask, val_mask, test_mask, num_classes,
                hidden_sizes):
    input_dim = features.shape[1]
    num_epochs = 200
    best_model = None

    model = model_class(input_dim, hidden_sizes, num_classes).to(features.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()

    best_val_acc = 0.0

    for epoch in range(num_epochs):
        model.train()
        logits = model(graph, features)
        loss = loss_fn(logits[train_mask], labels[train_mask])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if epoch % 50 == 0:
            val_acc, val_f1 = evaluate(model, graph, features, labels, val_mask)
            print(f"Epoch {epoch} | Loss {loss.item():.4f} | Val Acc {val_acc:.4f} | Val Macro-F1 {val_f1:.4f}")
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model = model  # 保存最佳模型

    return best_model


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    graph, features, labels, train_mask, val_mask, test_mask, papers = load_new_data(device)
    num_classes = len(torch.unique(labels[labels >= 0]))  # 忽略 -1 的占位符
    print("\n===== Training GCN =====")
    model = train_model(model_class=GCN, model_name='GCN', graph=graph, features=features, labels=labels,
                        train_mask=train_mask, val_mask=val_mask, test_mask=test_mask, num_classes=num_classes,
                        hidden_sizes=[256, 128])

    # 用最佳模型预测 2019 年及以后的标签
    model.eval()
    with torch.no_grad():
        logits = model(graph, features)
        _, predictions = torch.max(logits[test_mask], dim=1)
        papers.loc[test_mask.cpu().numpy(), 'category'] = predictions.cpu().numpy()

    # 保存补全后的文档
    papers['category'] = papers['category'].astype('category').cat.codes  # 恢复类别格式
    papers.to_csv('./dataset/papers_with_predictions.csv', index=False)
    print("Predictions saved to './dataset/papers_with_predictions.csv'")

    # 验证集准确率
    val_acc, val_f1 = evaluate(model, graph, features, labels, val_mask)
    print(f"Validation Accuracy: {val_acc:.4f} | Validation Macro-F1: {val_f1:.4f}")


if __name__ == '__main__':
    main()
