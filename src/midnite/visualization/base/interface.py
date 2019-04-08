from abc import ABC
from abc import abstractmethod
from typing import List
from typing import Optional

import torch
from numpy import ndarray
from torch import Tensor
from torch.nn import Module
from torch.nn import Sequential

import midnite


class LayerSplit(ABC):
    """Abstract base class for splits of a layer.

    A 'split' represents a way to 'slice the cube' of the spatial and
    channel positions of a layer. For more information, see
    https://distill.pub/2018/building-blocks/

    """

    @abstractmethod
    def invert(self):
        """Returns an inverted split"""
        raise NotImplementedError()

    @abstractmethod
    def get_split(self, size: List[int]) -> List[Tensor]:
        """Returns a split, i.e. all masks.

        Args:
            size: the size of the layer to split, usually as [c, h, w]

        Returns:
            a list of masks containing a mask for each split

        """
        raise NotImplementedError()

    @abstractmethod
    def get_mask(self, index: List[int], size: List[int]) -> Tensor:
        """Returns a single mask for the indexed split.

        Args:
            index: the index of the mask to get from the split
            size: the size of the layer to split, usually as [c, h, w]

        Returns:
            a single split mask

        """
        raise NotImplementedError()

    def get_mean(self, input_):
        """Returns the mean of an input along the split dimension.

        Args:
            input_: Tensor for which the mean should be computed
        Returns:
            a tensor of mean values.

        """
        output = torch.zeros_like(input_, device=midnite.get_device())
        for mask in self.get_split(input_.size()):
            norm = mask.sum()
            output.add_(mask.mul_(input_).div_(norm))
        return output

    @abstractmethod
    def fill_dimensions(self, input_):
        """Fills up the dimensions with unsqueeze(), so that output is (c, h, w).

        Args:
            input_: tensor which needs to be unsqueezed.
        Returns:
            the input_ with dimension (c, h, w)

        """
        raise NotImplementedError()


class NeuronSelector(ABC):
    @abstractmethod
    def get_mask(self, size: List[int]):
        """Get the mask for the specified neurons

        Args:
            size: size of the layer

        Returns:
            a mask of the selected neurons

        """
        raise NotImplementedError()


class Attribution(ABC):
    """Abstract base class for attribution methods.

    Attribution methods aim to extract insights about the effect that neurons in
    different layers have on each other.

    """

    def __init__(
        self,
        layers: List[Module],
        top_layer_selector: NeuronSelector,
        bottom_layer_split: LayerSplit,
    ):
        """
        Args:
            layers: the list of ajacent layers to execute the method on
            top_layer_selector: the target split for analyzing attribution
            bottom_layer_split: split of the selected layer

        """
        if len(layers) == 0:
            raise ValueError("Must specify at least one layer")
        self.net = Sequential(*layers)
        self.top_layer_selector = top_layer_selector
        self.bottom_layer_split = bottom_layer_split

    @abstractmethod
    def visualize(self, input_: Tensor) -> Tensor:
        """Abstract method to call attribution method

        Args:
            input_: the input tensor

        Returns: a tensor showing attribution

        """
        raise NotImplementedError()


class Activation(ABC):
    """Abstract base class for activation methods.

    Activation methods aim to visualize some properties of the activation of a layer or
    a number of layers.

    """

    def __init__(self, layers: List[Module], top_layer_selector: NeuronSelector):
        """
        Args:
            layers: the list of adjacent layers to execute the method on
            top_layer_selector: the split on which the activation properties are
             extracted

        """
        if len(layers) == 0:
            raise ValueError("Must specify at least one layer")
        self.net = Sequential(*layers)

        self.top_layer_selector = top_layer_selector

    @abstractmethod
    def visualize(self, input_: Optional[Tensor] = None) -> Tensor:
        """Visualizes an activation.

        Args:
            input_: an optional input image, usually a prior. Of shape (height, width,
             channels).

        Returns:
            an activation visualization of shape (h, w, c).

        """
        raise NotImplementedError()


class OutputRegularization(ABC):
    """Base class for regularizations on an output term."""

    def __init__(self, coefficient: float = 0.1):
        """
        Args:
            coefficient: how much regularization to apply

        """
        self.coefficient = coefficient

    @abstractmethod
    def loss(self, out: Tensor) -> Tensor:
        """Calculates the loss for an output.

         Args:
             out: the tensor to calculate the loss for, of shape
              (channels, height,width)

         Returns:
             a tensor representing the loss

         """
        raise NotImplementedError()


class TransformStep(ABC):
    """Abstract base class for an image transformation step"""

    @abstractmethod
    def transform(self, img: ndarray) -> ndarray:
        """Transforms the image.

        Args:
            img: the image to transform

        Returns:
            the transformed image

        """
        raise NotImplementedError()

    def __add__(self, other):
        """Method to easily concatenate two transformations.

        Args:
            other: the second transformation to apply

        Returns:
            a TransformSequence containing self and other

        """
        return TransformSequence(self, other)


class TransformSequence(TransformStep):
    """Concatenates a number of transform steps as a sequence."""

    def __init__(self, *steps: TransformStep):
        """
        Args:
            *steps: transformation steps to apply after each other

        """
        self.steps = steps

    def transform(self, img: ndarray) -> ndarray:
        for step in self.steps:
            img = step.transform(img)
        return img

    def __add__(self, other: TransformStep) -> TransformStep:
        self.steps += (other,)
        return self
