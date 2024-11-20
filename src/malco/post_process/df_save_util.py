import os
import shutil


def safe_save_tsv(path, filename, df):
    full_path = path / filename
    # If full_path already exists, prepend "old_"
    # It's the user's responsibility to know only up to 2 versions can exist, then data is lost
    if os.path.isfile(full_path):
        old_full_path = path / ("old_" + filename)
        if os.path.isfile(old_full_path):
            os.remove(old_full_path)
        shutil.copy(full_path, old_full_path)
        os.remove(full_path)
    df.to_csv(full_path, sep="\t", index=False)
