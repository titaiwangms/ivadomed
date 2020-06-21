from collections import defaultdict

from scipy import spatial
import numpy as np


class MetricManager(object):
    """
    Computes specified metrics and stores them in a dictionary

    Args:
        metric_fns (list): List of metric functions

    Attributes:
        metric_fns (list): List of metric functions
        result_dict (dict): Dictionary storing metrics
        num_samples (int): Number of samples
    """
    
    def __init__(self, metric_fns):
        self.metric_fns = metric_fns
        self.num_samples = 0
        self.result_dict = defaultdict(list)

    def __call__(self, prediction, ground_truth):
        self.num_samples += len(prediction)
        for metric_fn in self.metric_fns:
            for p, gt in zip(prediction, ground_truth):
                res = metric_fn(p, gt)
                dict_key = metric_fn.__name__
                self.result_dict[dict_key].append(res)

    def get_results(self):
        res_dict = {}
        for key, val in self.result_dict.items():
            if np.all(np.isnan(val)):  # if all values are np.nan
                res_dict[key] = None
            else:
                res_dict[key] = np.nanmean(val)
        return res_dict

    def reset(self):
        self.num_samples = 0
        self.result_dict = defaultdict(float)


def numeric_score(prediction, groundtruth):
    """Computation of statistical numerical scores:

    * FP = False Positives
    * FN = False Negatives
    * TP = True Positives
    * TN = True Negatives

    Args:
        prediction (nd.array): binary prediction
        groundtruth (nd.array): binary groundtruth

    Returns:
        float, float, float, float: FP, FN, TP, TN
    """
    FP = np.float(np.sum((prediction == 1) & (groundtruth == 0)))
    FN = np.float(np.sum((prediction == 0) & (groundtruth == 1)))
    TP = np.float(np.sum((prediction == 1) & (groundtruth == 1)))
    TN = np.float(np.sum((prediction == 0) & (groundtruth == 0)))
    return FP, FN, TP, TN


def dice_score(im1, im2, empty_score=np.nan):
    """Computes the Dice coefficient between im1 and im2.

    Compute a soft Dice coefficient between im1 and im2.
    If both images are empty, then it returns empty_score.

    Args:
        im1 (nd.array): First array.
        im2 (nd.array): Second array.
        empty_score (float): Returned value if both input array are empty.
    Returns:
        float: Dice coefficient.

    """
    im1 = np.asarray(im1)
    im2 = np.asarray(im2)

    if im1.shape != im2.shape:
        raise ValueError("Shape mismatch: im1 and im2 must have the same shape.")

    im_sum = im1.sum() + im2.sum()
    if im_sum == 0:
        return empty_score

    intersection = (im1 * im2).sum()
    return (2. * intersection) / im_sum


def mse(im1, im2):
    """ Compute the Mean Squared Error.

    Compute the Mean Squared Error between the two images, i.e. sum of the squared difference.

    Args:
        im1 (nd.array): First array.
        im2 (nd.array): Second array.
    Returns:
        float: Mean Squared Error.

    """
    im1 = np.asarray(im1)
    im2 = np.asarray(im2)

    if im1.shape != im2.shape:
        raise ValueError("Shape mismatch: im1 and im2 must have the same shape.")

    err = np.sum((im1.astype("float") - im2.astype("float")) ** 2)
    err /= float(im1.shape[0] * im1.shape[1])

    return err


def hausdorff_score(prediction, groundtruth):
    """
    Compute the directed Hausdorff distance between two N-D arrays.

    Args:
        prediction (nd.array): First array.
        groundtruth (nd.array): Second array

    Returns:
        float: hausdorff distance
    """
    if len(prediction.shape) == 4:
        n_classes, height, depth, width = prediction.shape
        # Reshape to have only 3 dimensions where prediction[:, idx, :] represents each 2D slice
        prediction = prediction.reshape((height, n_classes * depth, width))
        groundtruth = groundtruth.reshape((height, n_classes * depth, width))

    if len(prediction.shape) == 3:
        mean_hansdorff = 0
        for idx in range(prediction.shape[1]):
            pred = prediction[:, idx, :]
            gt = groundtruth[:, idx, :]
            mean_hansdorff += spatial.distance.directed_hausdorff(pred, gt)[0]
        mean_hansdorff = mean_hansdorff / prediction.shape[1]
        return mean_hansdorff

    return spatial.distance.directed_hausdorff(prediction, groundtruth)[0]


def precision_score(prediction, groundtruth, err_value=0.0):
    """
    Positive predictive value (PPV)

    Args:
        prediction (nd.array): First array.
        groundtruth (nd.array): Second array.
        err_value (float): value returned in case of error

    Returns:
        float: precision score

    """
    FP, FN, TP, TN = numeric_score(prediction, groundtruth)
    if (TP + FP) <= 0.0:
        return err_value

    precision = np.divide(TP, TP + FP)
    return precision


def recall_score(prediction, groundtruth, err_value=0.0):
    """
    True positive rate (TPR)

    Args:
        prediction (nd.array): First array.
        groundtruth (nd.array): Second array.
        err_value (float): value returned in case of error

    Returns:
        float: recall score
    """
    FP, FN, TP, TN = numeric_score(prediction, groundtruth)
    if (TP + FN) <= 0.0:
        return err_value
    TPR = np.divide(TP, TP + FN)
    return TPR


def specificity_score(prediction, groundtruth, err_value=0.0):
    """
    True negative rate (TNR)

    Args:
        prediction (nd.array): First array.
        groundtruth (nd.array): Second array.
        err_value (float): value returned in case of error

    Returns:
        float: specificity score
    """
    FP, FN, TP, TN = numeric_score(prediction, groundtruth)
    if (TN + FP) <= 0.0:
        return err_value
    TNR = np.divide(TN, TN + FP)
    return TNR


def intersection_over_union(prediction, groundtruth, err_value=0.0):
    """
    Intersection of two arrays over their union (IoU)

    Args:
        prediction (nd.array): First array.
        groundtruth (nd.array): Second array.
        err_value (float): value returned in case of error

    Returns:
        float: IoU
    """
    FP, FN, TP, TN = numeric_score(prediction, groundtruth)
    if (TP + FP + FN) <= 0.0:
        return err_value
    return TP / (TP + FP + FN)


def accuracy_score(prediction, groundtruth):
    """
    Accuracy

    Args:
        prediction (nd.array): First array.
        groundtruth (nd.array): Second array.

    Returns:
        float: accuracy

    """
    FP, FN, TP, TN = numeric_score(prediction, groundtruth)
    N = FP + FN + TP + TN
    accuracy = np.divide(TP + TN, N)
    return accuracy


def multi_class_dice_score(im1, im2):
    """
    Dice score for multi-label images

    Args:
        im1 (nd.array): First array.
        im2 (nd.array): Second array.

    Returns:
        float: multi-class dice
    """
    dice_per_class = 0
    n_classes = im1.shape[0]

    for i in range(n_classes):
        dice_per_class += dice_score(im1[i,], im2[i,], empty_score=1.0)

    return dice_per_class / n_classes
