#!/usr/bin/env python3
import random, string, hashlib, sys, os, re
import click
import pandas as pd
from unidecode import unidecode


@click.group()
def cli():
    pass


@cli.command()
@click.option("--chars", "-c", default=string.ascii_letters + string.digits,
              help="Character whitelist for generating a code.")
@click.option("--size", "-s", default=12,
              help="Code size.")
def generate(chars, size):
    """Generate a single random code."""
    code = "".join(random.choice(chars) for unused in range(size))
    click.echo(code)


def also_add_csv_map_command(**kwargs):
    def decorator(func):
        @cli.command(**kwargs)
        @click.argument("csvdf", metavar="CSV-FILE",
                        type=lambda f: pd.read_csv(f, sep=";",
                                                      keep_default_na=False))
        def csv_map_command(csvdf):
            for idx, row in csvdf.iterrows():
                click.echo(func(**row.to_dict()))
        return func
    return decorator


@also_add_csv_map_command(name="csv2msg")
def entry_message(name, code, category,
                  duration="", title="", extra="", **unused):
    return f"2018/Python-{category}_{code}_{unidecode(name).lower()}-Sudeste"


@also_add_csv_map_command(name="csv2hash")
def entry_hash(**kwargs):
    msg = entry_message(**kwargs).encode("utf-8")
    return hashlib.sha3_224(msg).hexdigest()


@also_add_csv_map_command(name="csv2pdf")
def entry_pdf(name, code, category, email,
              duration="", title="", extra="", outdir="certs", **unused):
    from reportlab.lib.colors import HexColor, black
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
    from reportlab.platypus import Paragraph, Frame, KeepInFrame, Spacer
    from svglib.svglib import svg2rlg

    registerFont(TTFont("Share", "Share-Regular.ttf"))
    registerFont(TTFont("ShareIt", "Share-Italic.ttf"))
    registerFontFamily("Share", normal="Share", italic="ShareIt")
    registerFont(TTFont("ShareMono", "Share-TechMono.ttf"))

    # Define text styles for the flowable text
    normal_style = ParagraphStyle(
        name="Normal",
        alignment=TA_CENTER,
        fontName="Share",
        fontSize=26,
        leading=26 * 1.2,
    )
    name_style = ParagraphStyle(
        name="NameStyle",
        parent=normal_style,
        fontSize=32,
        leading=32 * 1.2,
    )
    mono_style = ParagraphStyle(
        name="MonoStyle",
        alignment=TA_CENTER,
        fontName="ShareMono",
        fontSize=16,
        leading=16 * 1.2,
    )

    # Convert the inputs into actual text to be written
    category_text = {
        "ORG": "parte da organização",
        "COMUM": "participante",
        "PALESTRA": "palestrante",
        "TUTORIAL": "ministrante de tutorial",
        "KEYNOTE": "keynote",
    }["ORG" if category.startswith("ORG") else category]
    pyse_descr = (
        "terceira edição da Python Sudeste, realizada "
        "entre os dias 30 de março e 1 de abril de 2018 "
        "na cidade de São Paulo"
    )
    load_txt = f"com carga horária total de {duration}"
    main_txt = {
        "ORG": f"Fez parte da organização da {pyse_descr}, evento {load_txt}.",
        "COMUM": f"Participou da {pyse_descr}, evento {load_txt}.",
        "PALESTRA": f"Ministrou a palestra <i>{title}</i>, {load_txt}, "
                    f"durante a {pyse_descr}.",
        "TUTORIAL": f"Ministrou o tutorial <i>{title}</i>, {load_txt}, "
                    f"durante a {pyse_descr}.",
        "KEYNOTE": "Ministrou, na condição de <i>keynote</i> convidado, "
                  f"a palestra <i>{title}</i>, {load_txt}, "
                  f"durante a {pyse_descr}.",
    }["ORG" if category.startswith("ORG") else category]
    if extra and not extra.endswith("."):
        extra = extra + "."

    # Geometry and color constants
    height, width = A4
    borderw = .6 * cm
    yellowish = HexColor(0xfdd746)
    blueish = HexColor(0x356e9f)

    # Create the PDF file
    dname = os.path.join(outdir, email)
    os.makedirs(dname, exist_ok=True)
    category_ascii = category.lower() if category != "COMUM" else ""
    name_ascii = unidecode(name).lower().replace(" ", "-")
    title_ascii = re.sub("[^a-zA-Z0-9 ]", "",
                         unidecode(title).lower().replace(" ", "-"))
    joined_name = "_".join(filter(None,
        [name_ascii, category_ascii, title_ascii]))
    fname = os.path.join(dname, f"pyse218_cert_{joined_name}.pdf")
    c = canvas.Canvas(fname, pagesize=landscape(A4),
                      initialFontName=normal_style.fontName,
                      initialFontSize=normal_style.fontSize)

    # Helper function for adding the contents
    def add_frame(x, y_from_top, w, h, story):
        """Add a frame that auto-shrinks if required."""
        kif = KeepInFrame(maxWidth=w, maxHeight=h, content=story,
                          hAlign="CENTRE")
        f = Frame(x, height - y_from_top - h, w, h, showBoundary=0,
                  leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
        f.addFromList([kif], c)

    # Metadata
    c.setAuthor("Python Sudeste 2018")
    c.setCreator("CPython " + sys.version)
    c.setTitle(f"Certificado de {name} como {category_text} da PySE2018")
    c.setSubject("Certificado da Python Sudeste 2018")

    # Draws the Python logo as a "watermark" background
    py_logo = svg2rlg("logo_python_light.svg")
    py_logo_scale = min(width, height) \
                  / max(py_logo.minWidth(), py_logo.height) \
                  * .8
    py_logo.width = py_logo.minWidth() * py_logo_scale
    py_logo.height = py_logo.height * py_logo_scale
    py_logo.scale(py_logo_scale, py_logo_scale)
    add_frame((width - py_logo.width) / 2, (height - py_logo.height) / 2,
              py_logo.width, py_logo.height, [
        py_logo,
    ])

    # Draw the border
    c.setFillColor(yellowish)
    yb = c.beginPath()
    yb.moveTo(0, 0)
    yb.lineTo(0, height)
    yb.lineTo(width, height)
    yb.lineTo(width, (height + borderw) / 2)
    yb.lineTo(width - borderw, (height - borderw) / 2)
    yb.lineTo(width - borderw, height - borderw)
    yb.lineTo(borderw, height - borderw)
    yb.lineTo(borderw, borderw)
    yb.lineTo((width + borderw) / 2, borderw)
    yb.lineTo((width - borderw) / 2, 0)
    yb.close()
    c.drawPath(yb, stroke=0, fill=1)

    c.setFillColor(blueish)
    bb = c.beginPath()
    bb.moveTo(width, 0)
    bb.lineTo(width, (height + borderw) / 2)
    bb.lineTo(width - borderw, (height - borderw) / 2)
    bb.lineTo(width - borderw, borderw)
    bb.lineTo((width + borderw) / 2, borderw)
    bb.lineTo((width - borderw) / 2, 0)
    bb.close()
    c.drawPath(bb, stroke=0, fill=1)

    # Write the fixed text
    c.setFillColor(black)
    c.drawCentredString(width / 2, height - 6.35 * cm, "Certificamos que")

    # Write the flowable text
    add_frame(cm, 7.5 * cm, width - 2 * cm, 2 * cm, [
        Paragraph(name, name_style)
    ])

    add_frame(3 * cm, 10 * cm, width - 6 * cm, 8 * cm, [
        Paragraph(main_txt, normal_style),
        Spacer(cm, cm),
        Paragraph(extra, normal_style),
    ])

    # Draws the Python Sudeste 2018 logo
    pyse_logo = svg2rlg("logo_pyse2018.svg")
    pyse_logo_scale = 4
    pyse_logo.width = pyse_logo.minWidth() * pyse_logo_scale
    pyse_logo.height = pyse_logo.height * pyse_logo_scale
    pyse_logo.scale(pyse_logo_scale, pyse_logo_scale)
    add_frame(1.25 * cm, 1.25 * cm,
              pyse_logo.width, pyse_logo.height, [
        pyse_logo,
    ])

    # Draws the validation code
    check_url = "http://2018.pythonsudeste.org/certificados"
    add_frame(width * .0625, height - 2.125 * cm,
              width * .875, 1.5 * cm, [
        Paragraph("Valide em "
                  f'<link href="{check_url}">{check_url}</link>',
                  mono_style),
        Paragraph(f"Código: {code}", mono_style),
    ])

    c.save()
    return


if __name__ == "__main__":
    cli()
