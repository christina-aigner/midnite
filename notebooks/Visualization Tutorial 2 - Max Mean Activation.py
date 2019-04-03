#!/usr/bin/env python
# coding: utf-8

# In[ ]:


get_ipython().run_line_magic('matplotlib', 'inline')
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')
get_ipython().run_line_magic('cd', '../src')

from torchvision import models
from torch.nn.modules import Softmax
from matplotlib import pyplot as plt
import numpy as np
import torch
from plot_utils import show

import vinsight
from vinsight.visualization import *


# In[2]:


alexnet = models.alexnet(pretrained=True)


# # 1. Channel-wise regularization/transformation comparisons
# Here we will look at the effect of different regularizers.
# ## 1.1 No regularization

# In[3]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
).visualize())


# ## 1.2 Weight decay (l1)
# Less relevant parts of the image are set to zero.

# In[4]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    regularization = [WeightDecay(5e-6)]
).visualize())


# ## 1.3 Blur Filter
# Performs simple blurring after each step. Has the issue that edges are not preserved.

# In[5]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    transform = BlurTransform()
).visualize())


# ## 1.4 Bilateral Filter
# Like blur, but preserves edges.

# In[6]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    transform=BilateralTransform()
).visualize())


# ## 1.5 Random robustness transformations
# Apply random translation, rotation, and scaling after each iteration

# In[7]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    transform=RandomTransform()
).visualize())


# ## 1.6 Resizing transform
# After each iteration, scale the image up. This has the advantage that low-frequency patterns can be picked up better.

# In[8]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    transform=ResizeTransform(),
    init_size=50
).visualize())


# ## 1.7 Total Variation Regularizer
# Add total variation to the loss, which punishes difference in adjacent pixels.

# In[9]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    regularization=[TVRegularization(0.5)]
).visualize())


# # 2. Combining regularizers
#  - weight decay to gray out irrelevant parts
#  - blur (or biliteral filter) for penalizing high-frequency noise
#  - resizing to capture low-frequency patterns
#  - random transformations to get robust image
#  - total variation to get more natural looking image

# In[10]:


show(PixelActivation(
    alexnet.features[:9],
    NeuronSelector(ChannelSplit(), [1]),
    transform=RandomTransform()+BlurTransform()+ResizeTransform(),
    regularization=[TVRegularization(), WeightDecay(3e-7)],
    init_size=50
).visualize())


# # 3. Spatial and Individual Splits
# ## 3.1 Spatial
# Note how some parts of the image do not have any influence on the gradient, since the convolutions have not yet progressed as far.

# In[11]:


show(PixelActivation(
    alexnet.features[:6],
    NeuronSelector(SpatialSplit(), [3, 3]),
    transform=BlurTransform(),
    regularization=[WeightDecay(1e-6)]
).visualize())


# # 3.2 Individual Neurons

# In[13]:


show(PixelActivation(
    alexnet.features[:11],
    NeuronSelector(NeuronSplit(), [0, 0, 0]),
    transform=BlurTransform(),
    regularization=[WeightDecay(1e-7)]
).visualize())


# # 4. Class visualization
# Try to visualize class 783 (Screw)
# 
# TODO experiment (using a GPU) and add result here