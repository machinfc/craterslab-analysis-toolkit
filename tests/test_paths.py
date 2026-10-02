from toolkit.paths import get_dataset_dir, normalize_dataset_name


def test_normalize_dataset_name_aliases():
    assert normalize_dataset_name("fluidized") == "fluized"
    assert normalize_dataset_name("lroc") == "quickmap"


def test_get_dataset_dir_name():
    assert get_dataset_dir("compacted").name == "data_Compacted"
