source_files=oneflux_steps/ustar_cp_refactor_wip #/launch.m
target_dir="oneflux_steps/ustar_cp_py"

translate() {
    python smop/smop.py "$source_files" -d "$target_dir" -v
}

translate || {
    pip install -r smop/requirements.txt
    translate
}

cp smop/src/libsmop.py "$target_dir/libsmop.py"
find "$target_dir" -name "*.py" -exec 2to3 -x import -w -n {} +
ruff format "$target_dir"
ruff check "$target_dir" --fix
pytest tests #--pdb -n0