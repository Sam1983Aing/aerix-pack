"""Restore missing Stage 1 photos from their public sources (curl and Poppler)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

ROOT = Path(__file__).resolve().parents[1] / "references" / "real"
CDN = "https://se-cdn.djiits.com/tpc/uploads/carousel/image/"
STORE = {
    "mini-2": {
        "top": "ca5dea0049858e1e1e7f545e3c80770c",
        "front": "1f50ce8b01a883d94fb6a5198fbcfeb6",
        "folded": "748df6a18342503ab590b931327b10d9",
    },
    "mavic-air-2": {
        "top": "d69d6307fd912f9b28e7db1c0896106a",
        "front-elevated": "36686a09675382bfb57d7d12a3a1165f",
        "folded": "9487f3c511a70bd907673ba05bbc66af",
    },
}
EXHIBITS = {
    "mini-2": ("SS3-MT2WD2007/External-Photos/Photos-External-5784468",
               {"top-with-rulers": 0, "rear-battery-bay": 4}),
    "mavic-air-2": ("SS3-MA2UE1N1911/External-Photos/External-Photo-4681869",
                    {"front-folded": 16, "side-folded": 17, "underside-folded": 11}),
}
SIDE_PHOTO = "https://www.androidauthority.com/wp-content/uploads/2020/11/DJI-Mini-2-folded-side.jpg"


def download(url, destination):
    if destination.exists():
        return
    with TemporaryDirectory(dir=destination.parent) as tmp:
        payload = Path(tmp) / "download"
        subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                        "--max-time", "60", url, "--output", str(payload)], check=True)
        signature = b"%PDF" if destination.suffix == ".pdf" else b"\xff\xd8"
        if not payload.read_bytes().startswith(signature):
            raise ValueError(f"Unexpected file format at {url}")
        payload.replace(destination)


def main():
    for model, shots in STORE.items():
        folder = ROOT / model
        folder.mkdir(parents=True, exist_ok=True)
        for view, asset in shots.items():
            download(f"{CDN}{asset}@ultra.jpg", folder / f"{view}.jpg")
        exhibit, images = EXHIBITS[model]
        pdf = folder / "external.pdf"
        download(f"https://fccid.io/{exhibit}.pdf", pdf)
        missing = {folder / f"{name}.jpg": idx for name, idx in images.items()
                   if not (folder / f"{name}.jpg").exists()}
        if missing:
            with TemporaryDirectory(dir=folder) as tmp:
                subprocess.run(["pdfimages", "-j", str(pdf), f"{tmp}/image"], check=True)
                for destination, index in missing.items():
                    (Path(tmp) / f"image-{index:03}.jpg").replace(destination)
    download(SIDE_PHOTO, ROOT / "mini-2" / "side-folded.jpg")
    for side,image in (("right","P5366113"),("left","P5366115")):
        download(f"https://i.gzn.jp/img/2020/11/11/dji-mini-2/{image}.jpg",
                 ROOT / "mini-2" / f"open-{side}-gigazine.jpg")


if __name__ == "__main__":
    main()
