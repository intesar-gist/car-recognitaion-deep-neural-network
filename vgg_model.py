from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Flatten
from keras.layers.convolutional import Conv2D
from keras.optimizers import SGD
from keras.layers.pooling import MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense, ZeroPadding2D
from keras.callbacks import ModelCheckpoint,EarlyStopping
import cv2, numpy as np
from keras.utils import to_categorical
import load_data as compcar
from math import *
import os
import pickle
import matplotlib.pyplot as plt

label_encoder = None
batch_size = 128
num_classes = None
epochs_shortrun = 5
epochs_longrun = 500
label_encoder = None

save_dir = os.path.expanduser("~") + "/PycharmProjects/car-recognition-cnn/work"
res_dir = os.path.expanduser("~") + "/PycharmProjects/car-recognition-cnn/results"
model_name = "vgg_bmw"

ckpt_dir = os.path.join(save_dir,"checkpoints")
if not os.path.isdir(ckpt_dir):
    os.makedirs(ckpt_dir)

model_picture_path = os.path.join(res_dir, model_name + ".svg")
model_path = os.path.join(res_dir, model_name + ".kerasave")
hist_path = os.path.join(res_dir, model_name + ".kerashist")

def setup_load_compcar(verbose=False):
    global label_encoder
    # The data, shuffled and split between train and test sets:
    (x_train, y_train), (x_test, y_test), num_classes, label_encoder = compcar.load_data()
    if verbose:
        print("x_train shape: {}, {} train samples, {} test samples.\n".format(
            x_train.shape, x_train.shape[0], x_test.shape[0]))

    # Convert class vectors to binary class matrices.
    y_train = to_categorical(y_train, num_classes)
    y_test = to_categorical(y_test, num_classes)

    # Load label names to use in prediction results
    labels = compcar.load_labels()

    return x_train, y_train, x_test, y_test, labels


# Function to find latest checkpoint file
def last_ckpt(dir):
    fl = os.listdir(dir)
    fl = [x for x in fl if x.endswith(".hdf5")]
    cf = ""
    if len(fl) > 0:
        accs = [float(x.split("-")[3][0:-5]) for x in fl]
        m = max(accs)
        iaccs = [i for i, j in enumerate(accs) if j == m]
        fl = [fl[x] for x in iaccs]
        epochs = [int(x.split("-")[2]) for x in fl]
        cf = fl[epochs.index(max(epochs))]
        cf = os.path.join(dir, cf)

    return cf


# Visualizing CompCar, takes indicides and shows in a grid
def cifar_grid(X, Y, inds, n_col, predictions=None):
    import matplotlib.pyplot as plt
    if predictions is not None:
        if Y.shape != predictions.shape:
            print("Predictions must equal Y in length!\n")
            return (None)
    N = len(inds)
    n_row = int(ceil(1.0 * N / n_col))
    fig, axes = plt.subplots(n_row, n_col, figsize=(10, 10))

    clabels = labels["label_names"]
    for j in range(n_row):
        for k in range(n_col):
            i_inds = j * n_col + k
            i_data = inds[i_inds]

            axes[j][k].set_axis_off()
            if i_inds < N:
                axes[j][k].imshow(X[i_data, ...], interpolation="nearest")
                label = clabels[np.argmax(Y[i_data, ...])]
                axes[j][k].set_title(label)
                if predictions is not None:
                    pred = clabels[np.argmax(predictions[i_data, ...])]
                    if label != pred:
                        label += " n"
                        axes[j][k].set_title(pred, color="red")

    fig.set_tight_layout(True)
    return fig


def VGG_16(input_img_shape):
    print("Input image shape: " + str(input_img_shape) + "\n")
    model = Sequential()
    model.add(ZeroPadding2D((1,1), input_shape=input_img_shape))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(128, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(128, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(256, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(256, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(256, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(512, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(512, (3, 3), activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Conv2D(512, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(Flatten())
    model.add(Dense(4096, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(4096, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(18, activation='softmax'))

    return model

# im = cv2.resize(cv2.imread('cat.jpg'), (224, 224)).astype(np.float32)
# im[:,:,0] -= 103.939
# im[:,:,1] -= 116.779
# im[:,:,2] -= 123.68
# im = im.transpose((2,0,1))
# im = np.expand_dims(im, axis=0)

########################################
## # LOADING DATA FROM FILES
########################################
x_train, y_train, x_test, y_test, labels = setup_load_compcar(verbose=True)


#########################
## # TESTING LOADED DATA
#########################
def test_files():
    print(x_train[800].shape)
    print(y_train[800])
    print(label_encoder.inverse_transform([5]))
    print(labels.get(106))
    plt.imshow(x_train[800])
    plt.show()


# #######################################
# # SHOWING RANDOM CARD LOADED IN A GRID
# #######################################
# labels["label_names"] = ["abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde", "abcde"]
# indices = [np.random.choice(range(len(x_train))) for i in range(36)]
# fig = cifar_grid(x_train,y_train,indices,6)
# fig.show()


################################
## CREATING AND COMPILING MODEL
################################
model = VGG_16(x_train.shape[1:])
sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(optimizer=sgd, loss='categorical_crossentropy', metrics=["accuracy"])


##########################################
## SETTING UP CHECKPOINTS & EARLY STOPPING
##########################################
filepath = os.path.join(ckpt_dir, "weights-improvement-{epoch:02d}-{val_acc:.6f}.hdf5")
checkpoint = ModelCheckpoint(filepath, monitor="val_acc", verbose=1, save_best_only=True, mode="max")
print("Will save improvement checkpoints to \n\t{0}".format(filepath))

# early stop callback, given a bit more leeway
stahp = EarlyStopping(min_delta=0.00001, patience=25)


############################
## FITTING THE DATA TO model
############################

cpf = last_ckpt(ckpt_dir)
if cpf != "":
    print("Loading starting weights from \n\t{0}".format(cpf))
    model.load_weights(cpf)

epochs = epochs_longrun
hist = model.fit(x_train, y_train, epochs=epochs, validation_data=(x_test, y_test), callbacks=[checkpoint, stahp],
                 batch_size=64)


############################
## SAVE MODEL & WEIGHTS
############################
model.save(model_path)
print('Saved trained model at %s ' % model_path)

with open(hist_path, 'wb') as f:
    pickle.dump(hist.history, f)


print(np.argmax(hist))