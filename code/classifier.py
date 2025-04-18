import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np
import json
from collections import Counter

# Load the dataset from the JSON file
with open('checkpoint/checkpoint_new_0.3_GD3_3.0.json', 'r') as file:
    data = json.load(file)

# Extract features and labels from the dataset
z_scores = []
green_fractions = []
p_values = []
labels = []

for entry in data:
    if "output_without" in entry and "output_with" in entry:
        # Extract features for both watermarked and non-watermarked cases
        z_scores.append(entry["output_without"]["z_score"])
        green_fractions.append(entry["output_without"]["green_fraction"])
        p_values.append(entry["output_without"]["p_value"])
        labels.append(0)  # Label 0 for non-watermarked

        z_scores.append(entry["output_with"]["z_score"])
        green_fractions.append(entry["output_with"]["green_fraction"])
        p_values.append(entry["output_with"]["p_value"])
        labels.append(1)  # Label 1 for watermarked

# Convert lists to numpy arrays
z_scores = np.array(z_scores)
green_fractions = np.array(green_fractions)
p_values = np.array(p_values)
labels = np.array(labels)

# Check class distribution
print("Class distribution:", Counter(labels))

# Combine features into a single array
features = np.column_stack((z_scores, green_fractions, p_values))

# Standardize features
scaler = StandardScaler()
features = scaler.fit_transform(features)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42, stratify=labels)

# Convert data to PyTorch tensors
X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train, dtype=torch.long)
y_test_tensor = torch.tensor(y_test, dtype=torch.long)

# Define the neural network
class WatermarkClassifier(nn.Module):
    def __init__(self):
        super(WatermarkClassifier, self).__init__()
        self.fc1 = nn.Linear(3, 16)  # Input size is 3 (z_score, green_fraction, p_value)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 2)  # Output size is 2 (binary classification)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        return x

# Instantiate the model, define loss function and optimizer
model = WatermarkClassifier()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

# Training the model
num_epochs = 10000
for epoch in range(num_epochs):
    # Forward pass
    outputs = model(X_train_tensor)
    loss = criterion(outputs, y_train_tensor)

    # Backward pass and optimization
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if (epoch + 1) % 10 == 0:
        print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}")

# Evaluate the model
with torch.no_grad():
    y_pred_train = torch.argmax(model(X_train_tensor), dim=1)
    y_pred_test = torch.argmax(model(X_test_tensor), dim=1)

    train_accuracy = (y_pred_train == y_train_tensor).float().mean().item()
    test_accuracy = (y_pred_test == y_test_tensor).float().mean().item()

    train_precision = precision_score(y_train_tensor.numpy(), y_pred_train.numpy(), zero_division=1)
    train_recall = recall_score(y_train_tensor.numpy(), y_pred_train.numpy(), zero_division=1)
    train_f1 = f1_score(y_train_tensor.numpy(), y_pred_train.numpy(), zero_division=1)

    test_precision = precision_score(y_test_tensor.numpy(), y_pred_test.numpy(), zero_division=1)
    test_recall = recall_score(y_test_tensor.numpy(), y_pred_test.numpy(), zero_division=1)
    test_f1 = f1_score(y_test_tensor.numpy(), y_pred_test.numpy(), zero_division=1)

    print(f"Training Accuracy: {train_accuracy * 100:.2f}%")
    print(f"Testing Accuracy: {test_accuracy * 100:.2f}%")
    print(f"Training Precision: {train_precision:.4f}, Recall: {train_recall:.4f}, F1 Score: {train_f1:.4f}")
    print(f"Testing Precision: {test_precision:.4f}, Recall: {test_recall:.4f}, F1 Score: {test_f1:.4f}")

# Save the model
# torch.save(model.state_dict(), "watermark_classifier.pth")
