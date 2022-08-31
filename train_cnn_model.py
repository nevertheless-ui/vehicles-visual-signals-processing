"""
Training module for the project of vehicle signals recognition
Author: Filippenko Artyom, 2021-2022
MISIS Master Degree Project
"""
import keras
import tensorflow
import time
import argparse

from plot_keras_history import plot_history
from matplotlib import pyplot as plt

from keras.layers import Conv2D, BatchNormalization, MaxPool2D, GlobalMaxPool2D
from keras.layers import Dense, Dropout


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
    model.add(GlobalMaxPool2D())

    return model


def build_mobilenet(shape=(224, 224, 3)):
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


def build_efficentnet(shape=(224, 224, 3)):
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



def cnn_model(shape=(112, 112, 3)):
    momentum = .9

    # Feature extraction
    model = build_convnet()

    # Classification block
    model.add(Dense(2048, activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(Dropout(.5))
    model.add(Dense(1024, activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(Dropout(.5))
    model.add(Dense(128, activation='relu'))
    model.add(BatchNormalization(momentum=momentum))
    model.add(Dropout(.5))
    model.add(Dense(2, activation='softmax'))
    return model


def main():
    parser = argparse.ArgumentParser(description='TF CNN Model for vehicle image classification')
    parser.add_argument('--input', type=str, default="./dataset", metavar='N',
                        help='input batch size for training (default: ./dataset)')
    parser.add_argument('--batch-size', type=int, default=16, metavar='N',
                        help='input batch size for training (default: 16)')
    parser.add_argument('--test-batch-size', type=int, default=16, metavar='N',
                        help='input batch size for testing (default: 16)')
    parser.add_argument('--epochs', type=int, default=50, metavar='N',
                        help='number of epochs to train (default: 50)')
    parser.add_argument('--lr', type=float, default=0.005, metavar='LR',
                        help='learning rate (default: 0.005)')
    parser.add_argument('--lr-momentum', type=float, default=0.3, metavar='M',
                        help='Learning rate momentum (default: 0.3)')
    parser.add_argument('--patience', type=int, default=10,
                        help='Patience for early start')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='quickly check a single pass')
    args = parser.parse_args()

    # some global params
    SIZE = (112, 112) # Basic CNN, for MobilNet use (224, 224)
    CHANNELS = 3
    BS = args.batch_size
    TEST_BS = args.test_batch_size
    LR = args.lr
    LR_MOMENTUM = args.lr_momentum
    PATIENCE = args.patience

    if args.dry_run:
        EPOCHS = 1
    else:
        EPOCHS = args.epochs

    train = tensorflow.keras.utils.image_dataset_from_directory(
        f"{args.input}/train",
        color_mode='rgb',
        image_size=SIZE,
        batch_size=BS)

    valid = tensorflow.keras.utils.image_dataset_from_directory(
        f"{args.input}/test",
        validation_split=0.0,
        color_mode='rgb',
        shuffle=False,
        image_size=SIZE,
        batch_size=TEST_BS)

    INSHAPE=SIZE + (CHANNELS,) # (112, 112, 3)
    model = cnn_model(INSHAPE)

    optimizer = tensorflow.keras.optimizers.SGD(learning_rate=LR,
                                                momentum=LR_MOMENTUM,
                                                nesterov=True)

    model.compile(
        optimizer,
        loss=tensorflow.losses.SparseCategoricalCrossentropy(),
        metrics=['accuracy']
    )


    callbacks = [
        keras.callbacks.ReduceLROnPlateau(verbose=1,
                                          factor=0.3,
                                          patience=PATIENCE),
        keras.callbacks.ModelCheckpoint('chkp/weights.{epoch:02d}-{val_loss:.2f}.hdf5',
                                        verbose=1,
                                        save_best_only=True),
        keras.callbacks.EarlyStopping(monitor='val_loss',
                                      patience=((PATIENCE*2) + (PATIENCE//2))),
    ]
    history = model.fit(
        train,
        validation_data=valid,
        verbose=1,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    timestr = time.strftime("%Y-%m-%d--%H-%M-%S")
    plot_name = f"{timestr}_ep{EPOCHS}_batch{BS}_validBatch{TEST_BS}_lr{LR}" \
                f"_lrm{LR_MOMENTUM}_optADAM_CNN_patience{PATIENCE}.png"
    plot_history(history, path=f".//learning_histories//{plot_name}")
    plt.close()


if __name__ == '__main__':
    main()
