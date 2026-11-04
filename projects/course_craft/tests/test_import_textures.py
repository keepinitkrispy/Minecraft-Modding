"""Import-tool and validator tests. Run: python3 -m unittest discover -s tests -p 'test_*.py'"""
import io
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import import_textures  # noqa: E402
import validate  # noqa: E402


def png(size, color=(255, 0, 0, 255), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGBA" if fmt == "PNG" else "RGB", size, color[: 4 if fmt == "PNG" else 3]).save(buf, fmt)
    return buf.getvalue()


class ImportTests(unittest.TestCase):
    def setUp(self):
        # Work on a throwaway copy of the RP so real art is never touched.
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "packs"), os.path.join(self.tmp, "packs"))
        self._rp = import_textures.RP
        import_textures.RP = os.path.join(self.tmp, "packs", "CourseCraft_RP")

    def tearDown(self):
        import_textures.RP = self._rp
        shutil.rmtree(self.tmp)

    def _zip(self, files):
        path = os.path.join(self.tmp, "in.zip")
        with zipfile.ZipFile(path, "w") as zf:
            for name, data in files.items():
                zf.writestr(name, data)
        return path

    def test_valid_32px_import_replaces_slot_from_zip(self):
        src = self._zip({"art/cc_goal_top.png": png((32, 32)), "__MACOSX/._cc_goal_top.png": b"junk"})
        self.assertEqual(import_textures.run(src), 0)
        im = Image.open(import_textures.dest("cc_goal_top"))
        self.assertEqual(im.size, (32, 32))
        self.assertEqual(im.getpixel((0, 0)), (255, 0, 0, 255))

    def test_rejects_non_square_and_jpeg_and_bad_size(self):
        before = open(import_textures.dest("cc_shard"), "rb").read()
        src = self._zip({"cc_shard.png": png((16, 32)), "cc_cloud.png": png((16, 16), fmt="JPEG"), "cc_checkpoint.png": png((20, 20))})
        self.assertEqual(import_textures.run(src), 1)
        self.assertEqual(open(import_textures.dest("cc_shard"), "rb").read(), before)

    def test_unknown_names_skipped_not_fatal(self):
        d = os.path.join(self.tmp, "folder"); os.makedirs(d)
        open(os.path.join(d, "goomba.png"), "wb").write(png((16, 16)))
        open(os.path.join(d, "CC_CLOUD.png"), "wb").write(png((64, 64)))
        self.assertEqual(import_textures.run(d), 0)
        self.assertEqual(Image.open(import_textures.dest("cc_cloud")).size, (64, 64))

    def test_validator_passes_on_repo_and_after_import(self):
        self.assertEqual(validate.run(ROOT), 0)
        import_textures.run(self._zip({"cc_spike_top.png": png((128, 128))}))
        self.assertEqual(validate.run(self.tmp), 0)

    def test_validator_catches_missing_texture(self):
        os.remove(os.path.join(self.tmp, "packs", "CourseCraft_RP", "textures", "blocks", "cc_dash_top.png"))
        self.assertEqual(validate.run(self.tmp), 1)


if __name__ == "__main__":
    unittest.main()
