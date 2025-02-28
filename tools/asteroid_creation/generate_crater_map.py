"""
Script to generate a crater map composed of several craters.
"""

import os
from pathlib import Path
import argparse
import random
import numpy as np
import cv2
from PIL import Image
import thinplate as tps


def pick_random_points(h, w, n_samples):
    y_idx = np.random.choice(np.arange(h), size=n_samples, replace=False)
    x_idx = np.random.choice(np.arange(w), size=n_samples, replace=False)
    return y_idx/h, x_idx/w


def warp_dual_cv(img, mask, bg_mask, grad_im, c_src, c_dst):
    dshape = img.shape
    theta = tps.tps_theta_from_points(c_src, c_dst, reduced=True)
    grid = tps.tps_grid(theta, c_dst, dshape)
    mapx, mapy = tps.tps_grid_to_remap(grid, img.shape)
    return cv2.remap(img, mapx, mapy, cv2.INTER_CUBIC), cv2.remap(mask, mapx, mapy, cv2.INTER_NEAREST), cv2.remap(bg_mask, mapx, mapy, cv2.INTER_NEAREST), cv2.remap(grad_im, mapx, mapy, cv2.INTER_CUBIC)


def random_tps_warp(img, mask, bg_mask, grad_im, scale, n_ctrl_pts=12):
    """
    Apply a random TPS warp of the input image and mask
    Uses randomness from numpy
    """
    img = np.asarray(img)
    mask = np.asarray(mask)

    h, w = mask.shape
    points = pick_random_points(h, w, n_ctrl_pts)
    c_src = np.stack(points, 1)
    c_dst = c_src + np.random.normal(scale=scale, size=c_src.shape)
    warp_im, warp_gt, warp_bg, warp_grad = warp_dual_cv(img, mask, bg_mask, grad_im, c_src, c_dst)

    return warp_im, warp_gt, warp_bg, warp_grad


def get_gradient_image(h, w):
    # Create a meshgrid of coordinates (X, Y)
    X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))

    # Calculate the distance from the center (0, 0)
    distance = np.sqrt(X**2 + Y**2)

    # Normalize the distance so that the maximum distance from the center to a corner is 1
    max_distance = np.sqrt(2)  # Max distance is sqrt(1^2 + 1^2)
    distance_normalized = distance / max_distance

    # Invert the distance to create the gradient (1 in the center, 0 at the borders)
    gradient_image = 1 - distance_normalized

    # Clip the values to ensure they are between 0 and 1
    gradient_image = np.clip(gradient_image, 0, 1)
    border_max = np.stack((gradient_image[0], gradient_image[-1], gradient_image[:, 0], gradient_image[:, -1])).max()
    gradient_image -= border_max
    gradient_image[gradient_image < 0] = 0
    gradient_image = np.clip(gradient_image, 0, 1)
    gradient_image /= gradient_image.max()
    gradient_image -= 0.2
    gradient_image[gradient_image < 0] = 0.
    gradient_image /= gradient_image.max()

    return gradient_image


def rotate_image(image, angle, interpolation):
  image_center = tuple(np.array(image.shape[1::-1]) / 2)
  rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
  result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=interpolation)
  return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=4096)
    parser.add_argument('--border', type=int, default=64)
    parser.add_argument('--num-craters', type=int, default=20)
    parser.add_argument('--merge-type', type=str, default='mean_outside',
                        choices=['mean', 'mean_outside', 'argmax'])
    parser.add_argument('--data-root', type=str,
                        help='Path to the folder containing normalized crater dems and masks', required=True)
    parser.add_argument('--output-dir', type=str, required=True)
    args = parser.parse_args()

    cv2.setNumThreads(0)
    # default params
    min_xy_scale, max_xy_scale = 0.1, 1.
    min_height_scale, max_height_scale = 0.5, 1.5
    default_max_height = (65535 / max_height_scale) - 10
    tps_scale = 0.02
    tps_ctrl_pts = 12
    resize_factor_interpolation_grid = 4
    scale_factor = 8
    target_h, target_w = 512, 512

    canvas_ims = []
    canvas_masks = []
    canvas_bg_masks = []
    canvas_grad_ims = []

    assert args.merge_type in ['mean', 'mean_outside', 'argmax']
    assert max_height_scale * default_max_height <= 65535

    ims, masks, bg_masks, grad_ims = [], [], [], []
    for file in Path(args.data_root).glob('*_normalized.png'):
        mask = cv2.imread(file.as_posix().replace('_normalized', '_mask'), cv2.IMREAD_UNCHANGED)
        if mask.ndim == 3:
            mask = mask[:, :, 0]
        masks.append(mask)
        im = cv2.imread(file.as_posix(), cv2.IMREAD_UNCHANGED)
        h, w = im.shape
        # level image first
        border = np.concatenate([im[0], im[-1], im[1:-1, 0], im[1:-1, -1]]).mean()
        im = im.astype(np.float64) - float(border)
        im = im.astype(np.float64) #* gradient_image
        grad_im = get_gradient_image(h=h, w=w)
        grad_im[mask != 0] = 0
        grad_im = grad_im / grad_im.max()
        grad_ims.append(grad_im)
        ims.append(im)
    im_tmp = ims[0].astype(np.float64)
    im_tmp -= im_tmp.min()
    im_tmp /= im_tmp.max()

    height_scales = []

    for n in range(args.num_craters):
        # select a random crater
        crater_idx = np.random.randint(0, len(ims))
        crater_im = ims[crater_idx].copy()
        crater_mask = masks[crater_idx].copy()
        crater_mask[crater_mask != 0] = 1
        bg_mask = np.zeros_like(crater_mask)
        bg_mask[crater_mask == 0] = 1
        grad_im = grad_ims[crater_idx].copy()
        assert crater_im.shape[:2] == crater_mask.shape

        # rotation
        angle = np.random.randint(0, 360)
        crater_im = rotate_image(image=crater_im, angle=angle, interpolation=cv2.INTER_CUBIC)
        crater_mask = rotate_image(image=crater_mask, angle=angle, interpolation=cv2.INTER_NEAREST)
        bg_mask = rotate_image(image=bg_mask, angle=angle, interpolation=cv2.INTER_NEAREST)
        grad_im = rotate_image(image=grad_im, angle=angle, interpolation=cv2.INTER_NEAREST)

        # basic deformations / scaling / resizing
        resize_factor = random.uniform(min_xy_scale, max_xy_scale)
        h_s, w_s = int(target_h * resize_factor), int(target_w * resize_factor)
        crater_im = cv2.resize(crater_im, (w_s, h_s), interpolation=cv2.INTER_CUBIC)
        crater_mask = cv2.resize(crater_mask, (w_s, h_s), interpolation=cv2.INTER_NEAREST)
        bg_mask = cv2.resize(bg_mask, (w_s, h_s), interpolation=cv2.INTER_NEAREST)
        grad_im = cv2.resize(grad_im, (w_s, h_s), interpolation=cv2.INTER_NEAREST)

        # scaling
        height_scale_factor = random.uniform(min_height_scale, max_height_scale)
        height_scales.append(height_scale_factor)
        crater_im = crater_im * height_scale_factor

        # warping
        crater_im, crater_mask, bg_mask, grad_im = random_tps_warp(img=crater_im, mask=crater_mask, bg_mask=bg_mask,
                                                                   grad_im=grad_im, scale=tps_scale, n_ctrl_pts=tps_ctrl_pts)

        # paste onto image
        canvas_im = np.zeros((args.size, args.size), dtype=np.float64)
        canvas_mask = np.zeros((args.size, args.size), dtype=np.uint8)
        canvas_bg_mask = np.zeros((args.size, args.size), dtype=np.uint8)
        canvas_grad_im = np.zeros((args.size, args.size), dtype=np.float64)
        xloc = np.random.randint(args.border, args.size - args.border - w_s)
        yloc = np.random.randint(args.border, args.size - args.border - h_s)
        canvas_im[yloc:yloc + h_s, xloc:xloc + w_s] = crater_im
        canvas_mask[yloc:yloc + h_s, xloc:xloc + w_s] = crater_mask
        canvas_bg_mask[yloc:yloc + h_s, xloc:xloc + w_s] = bg_mask
        canvas_grad_im[yloc:yloc + h_s, xloc:xloc + w_s] = grad_im
        canvas_ims.append(canvas_im)
        canvas_masks.append(canvas_mask)
        canvas_bg_masks.append(canvas_bg_mask)
        canvas_grad_ims.append(canvas_grad_im)

    # merge
    final_canvas_im = np.zeros_like(canvas_ims[0])
    final_mask = np.zeros_like(canvas_ims[0], dtype=np.uint8)
    if args.merge_type == 'mean':
        overlaps = np.stack(canvas_masks).sum(axis=0)
        summed_canvas_im = np.stack(canvas_ims).astype(np.float64).sum(0)
        summed_canvas_im[overlaps != 0] /= overlaps[overlaps != 0]
        assert summed_canvas_im.max() <= 65535
        final_canvas_im = summed_canvas_im.astype(np.int16)
    elif args.merge_type == 'mean_outside':
        meaned_canvas_im = np.stack(canvas_ims).astype(np.float64)
        meaned_canvas_im[meaned_canvas_im == 0] = np.nan
        meaned_canvas_im = np.nanmean(meaned_canvas_im, axis=0)
        filter_area = np.zeros_like(final_canvas_im, dtype=np.uint8)
        # basically argmax, but only inside
        for cl_idx, (canvas_im, canvas_mask, canvas_bg_mask, canvas_grad_im) in enumerate(zip(canvas_ims, canvas_masks, canvas_bg_masks, canvas_grad_ims)):
            canvas_mask_eroded = cv2.dilate(canvas_mask.copy(), np.ones((7, 7), dtype=np.uint8), iterations=5)
            diff = (canvas_mask_eroded != canvas_mask).astype(np.uint8)
            final_canvas_im[canvas_mask != 0] = canvas_im[canvas_mask != 0]

            # for the outside: apply gradient merging
            canvas_grad_im[canvas_grad_im != 0] -= canvas_grad_im.min()
            canvas_grad_im[canvas_grad_im != 0] = canvas_grad_im[canvas_grad_im != 0] / canvas_grad_im.max()
            already_there = final_canvas_im[canvas_bg_mask != 0] * (1 - canvas_grad_im[canvas_bg_mask != 0])
            newly_added = canvas_im[canvas_bg_mask != 0] * canvas_grad_im[canvas_bg_mask != 0]
            final_canvas_im[canvas_bg_mask != 0] = already_there + newly_added

            # determine the area to filter later
            border = (cv2.dilate(canvas_bg_mask.copy(), np.ones((3, 3), dtype=np.uint8), iterations=1) != canvas_bg_mask).astype(np.uint8) * 255
            border[canvas_mask != 0] = 0
            border_dil = cv2.dilate(border, np.ones((5, 5)), iterations=5)
            filter_area[border_dil != 0] = 1

            k_size = 9
            kernel = np.ones((k_size, k_size), np.float32) / (k_size ** 2)
            filtered_canvas_im = cv2.filter2D(final_canvas_im.copy(), -1, kernel)
            final_mask[canvas_mask != 0] = (cl_idx + 1) * 10
    elif args.merge_type == 'argmax':
        for canvas_im in canvas_ims:
            final_canvas_im[canvas_im != 0] = canvas_im[canvas_im != 0]
    else:
        raise NotImplementedError(f"Unknown merge type: {args.merge_type}")

    final_canvas_im = cv2.normalize(final_canvas_im, None, 0, 65535, cv2.NORM_MINMAX, dtype=cv2.CV_16U)
    final_mask = np.stack((final_mask, final_mask, final_mask), axis=-1)

    # visualize generated results
    cv2.imshow('im', cv2.resize(final_canvas_im, (1024, 1024), interpolation=cv2.INTER_NEAREST) / final_canvas_im.max())
    cv2.imshow('mask', cv2.resize(final_mask, (1024, 1024), interpolation=cv2.INTER_NEAREST) / final_mask.max())
    cv2.waitKey(0)

    # save the generated maps
    os.makedirs(args.output_dir, exist_ok=True)
    im = Image.fromarray(final_canvas_im).save(f'{args.output_dir}/craters_disp_4k.png')
    cv2.imwrite(f'{args.output_dir}/label_mask.png', final_mask)
