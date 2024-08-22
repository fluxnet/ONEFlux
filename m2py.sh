source_files="oneflux_steps/ustar_cp/*.m"
target_dir="oneflux_steps/ustar_cp_py"

pip install -r smop/requirements.txt
python smop/smop.py $source_files -d $target_dir -v