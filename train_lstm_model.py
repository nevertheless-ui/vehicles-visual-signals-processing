"""
Training module for the project of vehicle signals recognition
Author: Filippenko Artyom, 2021-2022
MISIS Master Degree Project

TODO: ADD TENSORBOARD
"""


import os
import glob
import keras
import tensorflow
import time
import keras_video.utils
import argparse

from plot_keras_history import plot_history
from matplotlib import pyplot as plt
from keras_video import VideoFrameGenerator
from keras.layers import Conv2D, BatchNormalization, MaxPool2D, GlobalMaxPool2D
from keras.layers import TimeDistributed, Dense, Dropout, LSTM



def build_convnet(shape=(112, 112, 3)):
    momentum = .9
    model = keras.Sequential()
    model.add(Conv2D(64, (3,3), input_shape=shape, padding='same', activation='relu'))
    model.add(Conv2D(64, (3,3), padding='same', activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(MaxPool2D(pool_size=(3, 3)))

    model.add(Conv2D(128, (3,3), padding='same', activation='relu'))
    model.add(Conv2D(128, (3,3), padding='same', activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(MaxPool2D(pool_size=(3, 3)))

    model.add(Conv2D(256, (3,3), padding='same', activation='relu'))
    model.add(Conv2D(256, (3,3), padding='same', activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(MaxPool2D(pool_size=(3, 3)))

    model.add(Conv2D(512, (3,3), padding='same', activation='relu'))
    model.add(Conv2D(512, (3,3), padding='same', activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(MaxPool2D(pool_size=(3, 3)))

    model.add(Conv2D(1024, (3,3), padding='same', activation='relu'))
    model.add(Conv2D(1024, (3,3), padding='same', activation='relu'))
    model.add(BatchNormalization(momentum=momentum))

    # flatten...
    model.add(GlobalMaxPool2D())
    return model


def build_mobilenet(shape=(224, 224, 3), nbout=3):
    model = keras.applications.mobilenet.MobileNet(
        include_top=False,
        input_shape=shape,
        weights='imagenet')

    # Keep 9 layers to train
    trainable = 9
    for layer in model.layers[:-trainable]:
        layer.trainable = False
    for layer in model.layers[-trainable:]:
        layer.trainable = True
    output = tensorflow.keras.layers.GlobalMaxPool2D()
    return keras.Sequential([model, output])


def build_efficentnet(shape=(224, 224, 3), nbout=3):
    model = tensorflow.keras.applications.EfficientNetB7(
        include_top=False,
        weights='imagenet',
        input_shape=shape)

    # Keep 9 layers to train
    trainable = 9
    for layer in model.layers[:-trainable]:
        layer.trainable = False
    for layer in model.layers[-trainable:]:
        layer.trainable = True
    output = tensorflow.keras.layers.GlobalMaxPool2D()
    return keras.Sequential([model, output])


def action_model(shape=(5, 112, 112, 3), nbout=3, hidden_layers=64):
    momentum = .9
    # Create our convnet with (112, 112, 3) input shape
    convnet = build_convnet(shape[1:])
    #convnet = build_mobilenet(shape[1:])
    #convnet = build_efficentnet(shape[1:])

    # Classifictation LSTM blocs
    model = keras.Sequential()
    model.add(TimeDistributed(convnet, input_shape=shape))
    model.add(LSTM(1024, return_sequences=True))
    model.add(BatchNormalization(momentum=momentum))
    model.add(Dropout(.5))
    model.add(LSTM(128))
    model.add(BatchNormalization(momentum=momentum))
    model.add(Dropout(.5))
    model.add(Dense(nbout, activation='softmax'))

    return model


def main():
    parser = argparse.ArgumentParser(description="TF LSTM Model for vehicle image classification." \
                                                 " Must contain 'train' and 'test' dirs.")
    parser.add_argument('--input', type=str, default="./dataset", metavar='N',
                        help='input batch size for training (default: ./dataset)')
    parser.add_argument('--batch-size', type=int, default=30, metavar='N',
                        help='input batch size for training (default: 30)')
    parser.add_argument('--test-batch-size', type=int, default=30, metavar='N',
                        help='input batch size for testing (default: 30)')
    parser.add_argument('--epochs', type=int, default=1000, metavar='N',
                        help='number of epochs to train (default: 1000)')
    parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                        help='learning rate (default: 0.01)')
    parser.add_argument('--lr-momentum', type=float, default=0.3, metavar='M',
                        help='Learning rate momentum (default: 0.3)')
    parser.add_argument('--patience', type=int, default=150,
                        help='Patience for early start (default: 150)')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='quickly check a single pass')
    args = parser.parse_args()

    # Fix path string to avoid bugs with VideoFrameGenerator
    while '\\' in args.input:
        args.input = args.input.replace('\\', '/')

    # use sub directories names as classes
    classes = [i.split(os.path.sep)[1] for i in glob.glob(f'{args.input}/train/*')]
    classes.sort()

    # some global params
    SIZE = (112, 112) # Basic CNN (224, 224)  # MobilNet
    CHANNELS = 3
    NBFRAME = 5
    BS = args.batch_size
    TEST_BS = args.test_batch_size
    LR = args.lr
    LR_MOMENTUM = args.lr_momentum
    HL = 10000 # Hidden layers. Experimental
    PATIENCE = args.patience

    if args.dry_run:
        EPOCHS = 1
    else:
        EPOCHS = args.epochs


    # pattern to get videos and classes
    train_glob_pattern=f'{args.input}/train/' \
                        '{classname}/*.avi'
    test_glob_pattern=f'{args.input}/test/' \
                       '{classname}/*.avi'


    # for data augmentation
    data_aug = keras.preprocessing.image.ImageDataGenerator(
        #zoom_range=.1,
        horizontal_flip=True,
        #rotation_range=8,
        width_shift_range=.1,
        height_shift_range=.1)

    # Create video frame generator
    train = VideoFrameGenerator(
        classes=classes,
        glob_pattern=train_glob_pattern,
        nb_frames=NBFRAME,
        #split=.0,
        shuffle=True,
        batch_size=BS,
        target_shape=SIZE,
        nb_channel=CHANNELS,
        transformation=data_aug,
        use_frame_cache=True)

    valid = VideoFrameGenerator(
        classes=classes,
        glob_pattern=test_glob_pattern,
        nb_frames=NBFRAME,
        #split=.0,
        shuffle=False,
        batch_size=TEST_BS,
        target_shape=SIZE,
        nb_channel=CHANNELS,
        #transformation=data_aug,
        use_frame_cache=True)

    # TODO: Refactor for sample demonstration. Add flags?
    #keras_video.utils.show_sample(train)
    #keras_video.utils.show_sample(valid)
    #input()

    INSHAPE=(NBFRAME,) + SIZE + (CHANNELS,) # (5, 112, 112, 3)
    model = action_model(INSHAPE, len(classes), hidden_layers=HL)

    optimizer = tensorflow.keras.optimizers.Adam(LR)

    model.compile(
        optimizer,
        loss=tensorflow.keras.losses.BinaryCrossentropy(),
        metrics=[tensorflow.keras.metrics.BinaryAccuracy()]
    )

    # Create a "chkp" directory before to run that
    # As ModelCheckpoint will write models inside
    callbacks = [
        keras.callbacks.ReduceLROnPlateau(verbose=1, factor=0.5, patience=PATIENCE),
        keras.callbacks.ModelCheckpoint('chkp/weights.{epoch:02d}-{val_loss:.2f}.hdf5', verbose=1, save_best_only=True),
        #keras.callbacks.EarlyStopping(monitor='val_loss', patience=((PATIENCE*2) + (PATIENCE//2))),
    ]
    history = model.fit(
        train,
        validation_data=valid,
        verbose=1,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    timestr = time.strftime("%Y-%m-%d--%H-%M-%S")
    plot_history(history,
                 path=f".//learning_histories//{timestr}_ep{EPOCHS}_batch{BS}" \
                      f"_validBatch{TEST_BS}_lr{LR}_lrm{LR_MOMENTUM}_optADAM_LSTM{HL}" \
                      f"_patience{PATIENCE}.png")
    plt.close()


if __name__ == '__main__':
    main()
