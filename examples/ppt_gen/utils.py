import copy
import logging
import random

import matplotlib
from pptx.enum.shapes import MSO_SHAPE_TYPE

# rgb colors from a color scheme
_color_palette = [
    (178, 34, 34),    # 砖红
    (46, 139, 87),    # 海绿
    (70, 130, 180),   # 钢蓝
    (210, 180, 140),  # 棕褐
    (147, 112, 219),  # 中紫
    (255, 165, 0),    # 橙色（降饱和）
    (72, 209, 204),   # 青绿
    (205, 92, 92),    # 印度红
    (106, 90, 205),   # 板岩蓝
    (238, 130, 238),  # 紫罗兰
    (60, 179, 113),   # 中绿
    (100, 149, 237),  # 矢车菊蓝
    (218, 165, 32),   # 金
    (199, 21, 133),   # 深粉
    (65, 105, 225)    # 皇家蓝
]

def inspect_ppt(prs):
    for slide in prs.slides:
        inspect_slide(slide)

def inspect_slide(slide):
    def _inspect_shape_list(shapes, indent=0):
        for shape in shapes:
            print(" " * indent + shape.name)
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                _inspect_shape_list(shape.shapes, indent + 2)
    _inspect_shape_list(slide.shapes)

def to_svg(slide, prs, svg_filename="test.svg"):

    def _to_svg_box(shapes, svg_box):
        for shape in shapes:
            svg_box.append({
                "left": shape.left,
                "top": shape.top,
                "width": shape.width,
                "height": shape.height,
                "shape_type": shape.shape_type
            })
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                _to_svg_box(shape.shapes, svg_box)

    def render_svg(svg_box):
        width = prs.slide_width.inches
        height = prs.slide_height.inches
        fig, ax = matplotlib.pyplot.subplots(figsize=(width, height))
        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)
        for box in svg_box:
            left, top, width, height = box["left"].inches, box["top"].inches, box["width"].inches, box["height"].inches
            picked_color = random.choice(_color_palette)
            color = (picked_color[0] / 255, picked_color[1] / 255, picked_color[2] / 255, 0.3)
            ax.add_patch(matplotlib.patches.Rectangle((left, top), width, height, color=color))
        ax.set_axis_off()
        matplotlib.pyplot.subplots_adjust(left=0, right=1, top=1, bottom=0)  # 边距设为0
        matplotlib.pyplot.margins(0)  # 数据边距设为0
        ax.set_xmargin(0)  # x轴边距
        ax.set_ymargin(0)  # y轴边距
        fig.savefig(svg_filename, bbox_inches='tight', pad_inches=0)

    svg_box = []
    _to_svg_box(slide.shapes, svg_box)
    render_svg(svg_box)

    return svg_box

def delete_shape(shape):
    """
    Delete the given shape.
    """
    parent = shape.element.getparent()
    parent.remove(shape.element)

def find_shape_with_name(shapes, name, depth=0):
    """
    Find the shape with the given name in the given shapes.
    """
    if depth == 0:
        logging.info(f"Finding shape with name: {name}")
    for shape in shapes:
        if shape.name == name:
            return shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            found = find_shape_with_name(shape.shapes, name, depth + 1)
            if found:
                return found
    return None

def find_shape_with_name_except(shapes, name, depth=0):
    """
    Find the shape with the given name in the given shapes, except the shape with the given name.
    """
    if depth == 0:
        logging.info(f"Finding shape with name: {name}")
    for shape in shapes:
        if shape.name == name:
            return shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            found = find_shape_with_name(shape.shapes, name, depth + 1)
            if found:
                return found
    raise Exception(f"Shape with name {name} not found")

def duplicate_slide(prs, slide):
    """
    Copy the given slide to the end of the presentation.

    Args:
        prs: Presentation object
        slide: Slide object to be copied
    Returns:
        New created Slide object
    """
    # Create new slide, use the same layout
    slide_layout = slide.slide_layout
    new_slide = prs.slides.add_slide(slide_layout)

    # Copy all shapes
    for shape in slide.shapes:
        new_shape_element = copy.deepcopy(shape.element)
        new_slide.shapes._spTree.insert_element_before(new_shape_element, 'p:extLst')

    return new_slide

def delete_slide_range(prs, index_range):
    """delete slides in the given index range
    Args:
        prs: Presentation object
        index_range: range of slide indices (0-based)
    """
    for index in reversed(index_range):
        delete_slide(prs, index)

def delete_slide(prs, index):
    """delete slide at the given index
    Args:
        prs: Presentation object
        index: slide index (0-based)

    Raises:
        IndexError: when index out of range
    """
    if index < 0 or index >= len(prs.slides):
        raise IndexError(f"Slide index {index} out of range (0-{len(prs.slides)-1})")

    xml_slides = prs.slides._sldIdLst
    xml_slides.remove(xml_slides[index])

def move_slide(prs, old_index, new_index):
    """move slide from old_index to new_index"""
    xml_slides = prs.slides._sldIdLst
    # get the element to move
    slide_element = xml_slides[old_index]
    # remove the element from old position
    xml_slides.remove(slide_element)
    # insert to new position
    xml_slides.insert(new_index, slide_element)
    return prs
