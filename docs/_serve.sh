python3 _downsize.py --outputfolder assets_scaled --size 800
python3 _downsize.py --outputfolder assets --size 1600 --copynonimagefiles True

bundle exec jekyll serve
