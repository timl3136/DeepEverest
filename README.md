# DeepEverest: A System for Efficient DNN Interpretation

A prototype implementation of DeepEverest, which is a system that supports efficient DNN *interpretation by example* queries. DeepEverest focuses on accelerating two representative interpretation by example queries: "find the top-k inputs in the dataset that produce the highest activation value(s) for an individual neuron or a group of neurons specified by the user", and "for any input, find the k-nearest neighbors in the dataset using the activation values of a group of neurons based on the proximity in the latent space defined by the group of neurons specified by the user". We provide instructions on how you can apply DeepEverest to your own models and datasets [below](#ownmodel).

See [project website](https://db.cs.washington.edu/projects/deepeverest/) for more details. A [paper](http://vldb.org/pvldb/vol15/p98-he.pdf) for this project is published in PVLDB Vol. 15, [doi:10.14778/3485450.3485460](https://doi.org/10.14778/3485450.3485460). An [extended technical report](https://arxiv.org/abs/2104.02234) is also available.

## Repository Overview
An example notebook using the DeepEverest is `example_api.ipynb`. The implementation will also Implementations of core functionalities of DeepEverest are in `helper.py` and `index/deepeverst_index.cpp`. The DNN models and datasets used in the paper are in `models/`. However, you can apply DeepEverest on your own model and dataset. `index/` contains the core source for the construction of the indexes used in the DeepEverest. `tools/` contains useful interpretation techniques adapted from other projects. `utils.py` contains frequently used functions.

## Cloning
**Install [Git Large File Storage](https://git-lfs.github.com/) before cloning** the repository, then,

`git clone git@github.com:uwdb/DeepEverest.git` (or `git clone https://github.com/uwdb/DeepEverest.git` when ssh does not work) <br>

## Installation of required packages
The prototype is tested with Python 3.7. You can enter your virtual environment before this step.

`cd DeepEverest` <br>
`pip install -r requirements.txt`

## Example usage

### Build the dynamically linked library for the construction of the Neural Partition Index (NPI) and Maximum Activation Index (MAI) in DeepEverest
`cd index` <br>
`python setup_deepeverest_index.py build`

You should be able to see a `build` folder in your current directory. One of the directories (directory name depending on system and python versions) inside `build` will contain the built library. It is a `.so` file. The filename is also dependent on the system and python versions. For example, the relative path could look like `index/build/lib.macosx-10.7-x86_64-3.7/deepeverst_index.cpython-37m-darwin.so` if you build the library on a MacOS with an Intel CPU using Python 3.7.


### Use the DeepEverest (NPI and MAI)
Go to the root directory of DeepEverest. User could also refer to the `example_api.ipynb` to see how can it be used step by step.

User could use a package to load the pretrained model as well as the dataset to be queried on (Pytorch):

`model = Net()` <br>
`model = DeepEverest(model, True, lib_file, dataset)`

This is to load the model, and True for Pytorch, and False for tensorflow. lib_file is the path for the compiled c library, and dataset is the single dataset (torch tensor or numpy) for the query. 

Pretrained parameter can be loaded into the model by this statement:

`model.load_weights('mnist.pth')`

User could use the Deep Everest API for querying the top-k activations for a given image in a specific layer: 

`topk_activations = model.get_topk_activations_given_images([659], layer_name, 20)` <br>
`print(topk_activations)`

And the user could use Deep Everest API for querying the closest images for a given image with respect to a neuron group:

`top_k, exit_msg = model.answer_query_with_guarantee(layer_id, image_sample_id, 20, neuron_group)` <br>
`print(top_k)` <br>
`print(exit_msg)`

During the query, index will automatically constructed and persist in the memory, you can also store and load constructed indices to disk using the follow command:

`model.save_index_map("path")` <br>
`model.load_index_map("saved_map")`

### Interpret the functionalities of any group of neurons using DeepEverest's Neural Threshold Algorithm (NTA)

```
# Set the target input of interest and the number of top activations you want to inspect.
# For example, image 659 is a misclassified example in the dataset.
image_ids = [659]
n_neurons = 5

# Get the top-k activations for this input in this layer and their corresponding neuron IDs.
from utils import get_topk_activations_given_images

topk_activations = get_topk_activations_given_images(model, dataset, image_ids, layer_name, n_neurons)[0]
topk_activations_neurons = [x[1] for x in topk_activations]

# Construct the group of neurons that you are interested in, e.g., the top-3 maximally activated neurons.
from NeuronGroup import *

image_sample_id = image_ids[0]
neuron_group = NeuronGroup(model.model, layer_id, neuron_idx_list=topk_activations_neurons[:3])

# Query for the k-nearest neighbors in the dataset using the activations of this group of neurons
# based on the proximity in the latent space defined by this group of neurons.
# answer_query_with_guarantee() runs the Neural Threshold Algorithm.
from DeepEverest import answer_query_with_guarantee

k = 20
top_k, exit_msg, _, n_images_run = answer_query_with_guarantee(
                                    model, dataset, rev_act, rev_idx_act, rev_bit_arr, rev_idx_idx,
                                    par_l_bnd, par_u_bnd, image_sample_id, neuron_group, k,
                                    n_partitions, bits_per_image, BATCH_SIZE=batch_size, batch_size=batch_size)
                                    

# Sort the top-k results based on their negative distances to the target input.
top_k = sorted(top_k)

# Visualize the top-k results.
from utils import plot_mnist

for neg_dist, image_id in top_k:
    plot_mnist(x_test, label_test, image_id)
```

The top-k results in `top_k`. Inspect them to investigate and understand the group of neurons' functionality by tying that functionality to the input examples in the dataset.

## Running the example notebook
You can run `example_api.ipynb` to walk through the functionalities that DeepEverest provides. `old-examples/` also contains a few more examples for an old version of DeepEverest with some other useful interpretation techniques adapted from other projects (e.g., pixel-level attribution), which probably only works with Tensorflow 1.x.

## Working with your own model <a name="ownmodel"></a>
To apply DeepEverest on your own raw model (currently supporting `tf.keras` models), create a subclass of `BaseModel` in `models/` because DeepEverest relies on methods of `BaseModel`. For example, create a file `CustomModel.py` in `models/`,

```
from models.BaseModel import BaseModel

class CustomModel(BaseModel):
    def __init__(self, model):
        BaseModel.__init__(self, model=model, optimizer=None)
    def preprocess_input_for_inference(self, x):
        return x
```

In your main script, load your own raw model and wrap it in `CustomModel` so that DeepEverest can work.

```
from tensorflow.keras.models import load_model
from models.CustomModel import CustomModel

raw_model = load_model('your_own_model.h5')
model = CustomModel(raw_model)
```

Yay, now you can use DeepEverest with `model`.

## Updated: Support for Pytorch and TensorFlow model
DeepEverest now support both Pytorch and TensorFlow model, the instruction of using can be seen from the example_api.ipynb notebook. Both model can be run from the new DeepEverestAPI class, which is a relatively integrated environment. They can also be run from the normal step by step way as shown in the example.ipynb and example_torch.ipynb notebooks. 

## Citations & Paper

If you find DeepEverest useful, please cite our paper:

_DeepEverest: Accelerating Declarative Top-K Queries for Deep Neural Network Interpretation_<br />
Dong He, Maureen Daum, Walter Cai, Magdalena Balazinska<br />
Proc. VLDB Endow. 15(1): 98-111 (2021) [[PDF]](https://doi.org/10.14778/3485450.3485460)

```
@article{DBLP:journals/pvldb/HeDCB21,
  author    = {Dong He and
               Maureen Daum and
               Walter Cai and
               Magdalena Balazinska},
  title     = {DeepEverest: Accelerating Declarative Top-K Queries for Deep Neural
               Network Interpretation},
  journal   = {Proc. {VLDB} Endow.},
  volume    = {15},
  number    = {1},
  pages     = {98--111},
  year      = {2021},
  url       = {http://www.vldb.org/pvldb/vol15/p98-he.pdf},
  biburl    = {https://dblp.org/rec/journals/pvldb/HeDCB21.bib}
}
```

See the [project website](https://db.cs.washington.edu/projects/deepeverest/) for more details about DeepEverest.

