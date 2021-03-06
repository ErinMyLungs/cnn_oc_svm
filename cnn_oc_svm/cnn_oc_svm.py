# AUTOGENERATED! DO NOT EDIT! File to edit: 00_cnn_oc_svm.ipynb (unless otherwise specified).

__all__ = ['cnn_oc_svm', 'create_basic_neural_net_structure']

# Cell
import numpy as np
import copy
import torch
import torchvision
import matplotlib.pyplot as plt
from torchvision import datasets, transforms
from torch import nn, optim
import time
from pathlib import Path
from typing import List
from sklearn.svm import OneClassSVM


class cnn_oc_svm:
    """
    The base-class for building a neural network with oc-SVM.
    """

    def __init__(self, neural_net, criterion, optimizer):
        self.neural_net = neural_net
        self.criterion = criterion
        self.optimizer = optimizer

        self.original_transforms = None
        self.oc_svm = None

    def training(self, epochs, learning_rate, training_data_loader, *args, **kwargs):
        """
        Basic training function for nn.Sequence style models.
        """
        start_time = time.time()
        for epoch in range(1, epochs + 1):
            running_loss = 0
            for images, labels in training_data_loader:
                images = images.view(images.shape[0], -1)

                optimizer.zero_grad()

                predicted_labels = self.neural_net(images)
                loss = self.criterion(predicted_labels, labels)

                loss.backward()

                optimizer.step()

                running_loss += loss.item()

            else:
                print(
                    f"Epoch {epoch} - Training loss: {running_loss/len(training_data_loader)}"
                )

        print(f"Training time (s): {time.time()-start_time}")
        return running_loss / len(training_data_loader)

    def evaluation(self, validation_data_loader):
        """
        Simple evaluation function to check neural network accuracy
        """
        correct_classification, total_count = 0, 0
        for images, labels in validation_data_loader:
            for i in range(len(labels)):
                img = images[i].view(1, 784)

                with torch.no_grad():  # no grad because we are evaluation mode! using .eval() might work too
                    log_probabilities = model(img)
                probabilities = list(torch.exp(log_probabilities).numpy()[0])

                predicted_label = probabilities.index(max(probabilities))
                true_label = labels.numpy()[i]

                if predicted_label == true_label:
                    correct_classification += 1

                total_count += 1
        print(
            f"Images tested: {total_count} \n Classification Accuracy: {correct_classification/total_count}"
        )
        return correct_classification / total_count

    def train_oc_svm(self, training_data_loader, amount_to_train_on=None):

        start_time = time.time()

        image_to_feature_transform = self.neural_net[:-2].eval()
        # load up our to numpy and image to feature vector transforms
        oc_svm_data_transforms = transforms.Compose(
            [
                lambda x: x.view(-1, 28 ** 2),
                lambda x: image_to_feature_transform(x),
                lambda x: x.detach().numpy(),
                lambda x: x.flatten(),
            ]
        )

        training_data = list()
        if amount_to_train_on == None:
            amount_to_train_on = len(training_data_loader.dataset)
        while len(training_data) < amount_to_train_on:
            image, _ = next(iter(training_data_loader))
            training_data.extend([oc_svm_data_transforms(im) for im in image])
        training_data = np.array(training_data)

        self.oc_svm = OneClassSVM()
        print(f"Fitting One Class SVM on {len(training_data)} data points")
        self.oc_svm.fit(training_data)

        if self.oc_svm.fit_status_ != 0:
            print(f"OC SVM incorrectly fitted, try refitting?")
        else:
            print(f"OC SVM Sucessfully fit, training time: {time.time()-start_time}")

    def predict_if_outlier(self, predict_data_loader):
        image_to_feature_transform = self.neural_net[:-2].eval()

        oc_svm_data_transforms = transforms.Compose(
            [
                lambda x: x.view(-1, 28 ** 2),
                lambda x: image_to_feature_transform(x),
                lambda x: x.detach().numpy(),
                lambda x: x.flatten(),
            ]
        )
        predictions = list()
        for image in next(iter(predict_data_loader))[0]:
            predictions.extend([oc_svm_data_transforms(im) for im in image])
        results = self.oc_svm.predict(predictions)
        return results

    def __repr__(self):
        return self.neural_net.__repr__()

# Cell
def create_basic_neural_net_structure(
    input_size=28 * 28, hidden_sizes=[128, 64], number_of_classes=10
):
    """
    Creates basic neural network with an input layer, feature extraction layer, and output layer.
    Basic structure:
        Input: linear layer of image resolution (color * width * height) and ReLU activation
        Hidden: linear layer of hidden sizes and RelU activation
        Output: liear layer and LogSoftmax activation to final size of number_of_classes
    parameters:
        input_size: number of neurons in input layer
        hidden_sizes: in_feature and out_feature sizes as ints.
    returns: Sequential neural net for training and inference.
    """
    if not isinstance(input_size, int):
        raise TypeError(
            f"Input size must be an integer, received type {type(input_size)}"
        )
    if input_size <= 0:
        raise ValueError(
            f"Input must be greater than 0 and an integer, received {input_size}"
        )

    input_layer_dimensions = (
        (input_size, hidden_sizes[0])
        if len(hidden_sizes) != 0
        else (input_size, number_of_classes)
    )
    input_layers = [nn.Linear(*input_layer_dimensions), nn.ReLU()]

    if len(hidden_sizes) == 0:
        hidden_layers = list()
    else:
        hidden_layers = [
            layer
            for dims in zip(hidden_sizes[:-1], hidden_sizes[1:])
            for layer in (nn.Linear(*dims), nn.ReLU())
        ]

    final_output_layer_dimensions = (
        (hidden_sizes[-1], number_of_classes)
        if len(hidden_sizes) != 0
        else (input_size, number_of_classes)
    )

    final_output_layer = [nn.Linear(*final_output_layer_dimensions), nn.LogSoftmax()]

    model_structure_list = list()
    for structure in [input_layers, hidden_layers, final_output_layer]:
        model_structure_list.extend(structure)

    model = nn.Sequential(*model_structure_list)

    return model