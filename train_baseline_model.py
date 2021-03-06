from __future__ import print_function
import argparse
import os
import csv
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from torchvision import datasets, transforms
from torch.optim.lr_scheduler import StepLR
from torch.utils.tensorboard import SummaryWriter
from utils import logging_tool


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def train(args, model, device, train_loader, optimizer, epoch, logger):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % args.log_interval == 0:
            proccessed_examples = batch_idx * len(data)
            examples_total = len(train_loader.dataset)
            examples_total_in_percents = round(100. * batch_idx / len(train_loader))
            total_loss_value = round(loss.item(), 6)
            log_msg = \
                f"Train Epoch: {epoch} [{proccessed_examples}/{examples_total} " \
                f"({examples_total_in_percents}%)]\tLoss: {total_loss_value}"
            logger.debug(log_msg)
            print(log_msg)
            if args.dry_run:
                break


def test(model, device, test_loader, epoch, logger, models_path, tensorboard_writer):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    test_loss = round(test_loss, 4)
    accuracy_state = round(correct / len(test_loader.dataset), 3)
    tensorboard_writer.add_scalar("Loss/train", test_loss, epoch)
    #tensorboard_writer.add_scalar("Loss/train", loss, epoch)

    with open(os.path.join(models_path, 'training_history.csv'), 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow([epoch, test_loss, accuracy_state])

    accuracy_percentage = round(100. * correct / len(test_loader.dataset), 2)
    log_msg = \
        f"Test set: Average loss: {test_loss}, " \
        f"Accuracy: {correct}/{len(test_loader.dataset)} ({accuracy_percentage}%)"

    logger.debug(log_msg)
    print(log_msg)
    model_path = os.path.join(models_path, f"mnist_cnn_epoch_{epoch}.pt")
    logger.debug(f"Saving model parameters to: {model_path}")
    torch.save(model.state_dict(), model_path)


def main():
    # Training settings
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=14, metavar='N',
                        help='number of epochs to train (default: 14)')
    parser.add_argument('--lr', type=float, default=1.0, metavar='LR',
                        help='learning rate (default: 1.0)')
    parser.add_argument('--gamma', type=float, default=0.7, metavar='M',
                        help='Learning rate step gamma (default: 0.7)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='quickly check a single pass')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument('--log-interval', type=int, default=50, metavar='N',
                        help='how many batches to wait before logging training status')
    parser.add_argument('--save-model', action='store_true', default=True,
                        help='For Saving the current Model')
    args = parser.parse_args()

    use_cuda = not args.no_cuda and torch.cuda.is_available()
    torch.manual_seed(args.seed)
    logger = logging_tool.get_logger()
    models_path = f"./models/history/{logger.name}"
    os.makedirs(models_path)
    tensorboard_writer = SummaryWriter()


    device = torch.device("cuda" if use_cuda else "cpu")
    train_kwargs = {'batch_size': args.batch_size}
    test_kwargs = {'batch_size': args.test_batch_size}
    if use_cuda:
        cuda_kwargs = {'num_workers': 0,
                       'pin_memory': True,
                       'shuffle': True}
        train_kwargs.update(cuda_kwargs)
        test_kwargs.update(cuda_kwargs)

    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
        ])
    dataset1 = datasets.MNIST('../data', train=True, download=True,
                       transform=transform)
    dataset2 = datasets.MNIST('../data', train=False,
                       transform=transform)
    train_loader = torch.utils.data.DataLoader(dataset1,**train_kwargs)
    test_loader = torch.utils.data.DataLoader(dataset2, **test_kwargs)

    model = Net().to(device)
    optimizer = optim.Adadelta(model.parameters(), lr=args.lr)
    scheduler = StepLR(optimizer, step_size=1, gamma=args.gamma)

    model_info_path = os.path.join(models_path, "model_info.txt")

    with open(model_info_path, 'a') as model_info_file:
        for param in (model, optimizer):
            model_info_file.write(str(param))

    with open(os.path.join(models_path, 'training_history.csv'), 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['Epoch', 'Loss', 'Accuracy'])

    for epoch in range(1, args.epochs + 1):
        train(args, model, device, train_loader, optimizer, epoch, logger)
        test(model, device, test_loader, epoch, logger, models_path, tensorboard_writer)
        scheduler.step()

    if args.save_model:
        model_path = os.path.join(models_path, "mnist_cnn_final_model.pt")
        logger.debug(f"Saving full model to: {model_path}")
        torch.save(model.state_dict(), model_path)


if __name__ == '__main__':
    main()
