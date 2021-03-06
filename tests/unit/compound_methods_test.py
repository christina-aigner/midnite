"""Unit test for the compound methods."""
import pytest
import torch
from assertpy import assert_that
from numpy.testing import assert_array_equal
from torch.nn import functional
from torch.nn import Module

from midnite.visualization import compound_methods
from midnite.visualization.compound_methods import _prepare_input
from midnite.visualization.compound_methods import _top_k_mask
from midnite.visualization.compound_methods import _top_k_selector
from midnite.visualization.compound_methods import _upscale
from midnite.visualization.compound_methods import guided_gradcam


@pytest.fixture
def img(mocker):
    img = torch.zeros((1, 3, 4, 4))
    img.detach = mocker.Mock(return_value=img)
    img.to = mocker.Mock(return_value=img)
    return img


def test_prepare_input(img, mocker):
    """Test image preparations."""
    img_clone = torch.tensor((1, 3, 4, 4))
    img_clone.clone = mocker.Mock(return_value=img)
    out = _prepare_input(img_clone)

    img_clone.clone.assert_called_once()
    img.detach.assert_called_once()
    img.to.assert_called_once()
    assert_that(out).is_same_as(img)


def test_prepare_invalid_sizes():
    """Test errors for input that are not images."""
    with pytest.raises(ValueError):
        _prepare_input(torch.zeros((2, 4, 4)))
    with pytest.raises(ValueError):
        _prepare_input(torch.zeros(1, 2, 4, 4))
    with pytest.raises(ValueError):
        _prepare_input(torch.zeros(2, 3))


def test_top_k_mask():
    """Test top-k masking."""
    out = torch.tensor([0, 3, 0, 2, 1, 0])
    mask = _top_k_mask(out, 2)
    assert_array_equal(mask, [0, 1, 0, 1, 0, 0])


def test_top_k_selector(mocker):
    """Test that the selector predicts and selects"""
    out = mocker.Mock(spec=torch.Tensor)
    out.squeeze = mocker.Mock(return_value=out)
    net = mocker.Mock(spec=Module, return_value=out)
    net.to = mocker.Mock(return_value=net)
    net.eval = mocker.Mock(return_value=net)
    mask = torch.tensor((0, 1, 0))
    mocker.patch(
        "midnite.visualization.compound_methods._top_k_mask", return_value=mask
    )

    sel = _top_k_selector(net, mocker.Mock(spec=torch.Tensor), 5)

    compound_methods._top_k_mask.assert_called_with(out, 5)
    assert_that(sel.get_mask([3])).is_same_as(mask)


def test_upscale(mocker):
    """Check upscale wiring."""
    scaled = torch.zeros((4, 4))
    scaled.squeeze = mocker.Mock(return_value=scaled)
    mocker.patch("torch.nn.functional.interpolate", return_value=scaled)
    img = torch.zeros(2, 2)
    img.unsqueeze = mocker.Mock(return_value=img)

    res = _upscale(img, (4, 4))

    functional.interpolate.assert_called_with(
        img, size=(4, 4), mode="bilinear", align_corners=True
    )
    assert_that(res).is_same_as(scaled)
    assert_that(scaled.squeeze.call_count).is_equal_to(2)
    assert_that(img.unsqueeze.call_count).is_equal_to(2)


def test_guided_gradcam(mocker):
    """Check the guided gradcam wiring."""
    input_ = torch.zeros((3, 5, 5))
    gradcam_out = torch.ones((5, 5)).mul_(2)
    backprop_out = torch.ones((5, 5)).mul_(3)
    mocker.patch(
        "midnite.visualization.compound_methods.gradcam", return_value=gradcam_out
    )
    mocker.patch(
        "midnite.visualization.compound_methods.guided_backpropagation",
        return_value=backprop_out,
    )

    res = guided_gradcam([mocker.Mock(spec=Module)], [mocker.Mock(spec=Module)], input_)

    compound_methods.gradcam.assert_called_once()
    compound_methods.gradcam.assert_called_once()
    assert_that(res.size()).is_equal_to((5, 5))
    assert_that(res.sum()).is_equal_to(5 * 5 * 6)
