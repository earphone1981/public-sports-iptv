from pathlib import Path
import cairosvg

BASE = Path(__file__).resolve().parent / 'public_sports_logos_github_43' / 'jra_quality'


def main():
    svgs = sorted(BASE.glob('*.svg'))
    if len(svgs) != 8:
        raise SystemExit(f'Expected 8 JRA SVG logos, found {len(svgs)}')

    for src in svgs:
        dst = src.with_suffix('.png')
        cairosvg.svg2png(
            url=str(src),
            write_to=str(dst),
            output_width=1024,
            output_height=1024,
        )
        print(f'{src.name} -> {dst.name} ({dst.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
