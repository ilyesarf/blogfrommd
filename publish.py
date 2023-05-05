import os, shutil
import markdown
from collections.abc import Iterable

class Utils:
    @classmethod
    def flatten(cls, arr):
        lis = []
        for item in arr:
            if isinstance(item, Iterable) and not isinstance(item, str):
                for x in cls.flatten(item):
                    lis.append(x) 
            else:         
                 lis.append(item)
        
        return lis

    @staticmethod
    def replace_md(f): return os.path.splitext(f)[0]

class Convert:
    def __init__(self, src_dir="site", dist_dir="."):
        self.utils = Utils
        self.src_dir = src_dir
        self.dist_dir = dist_dir
    
    
    def compare_content(self):
        filter_dir = lambda d: self.src_dir not in d and '.' not in d
        filter_file = lambda f: f[0] != '.' and any(ext in f for ext in ['html', 'md', 'markdown'])

        site_cc = self.utils.flatten([[self.src_dir+'/'+d for d in list(filter(lambda d: '.' not in d, dirs))] + [os.path.join(subdir, f) for f in files] for subdir, dirs, files in os.walk(self.src_dir)])

        dist_cc = [] #current content
        for subdir, dirs, files in os.walk(self.dist_dir):
            if filter_dir(subdir[2:]):
                dist_cc.extend(self.utils.flatten([self.dist_dir+'/'+d for d in list(filter(filter_dir, dirs))] + [os.path.join(subdir, os.path.splitext(f)[0]) for f in list(filter(filter_file, files))]))     
        
        return [c for c in site_cc if self.utils.replace_md(c.replace('site/', './')) not in dist_cc] +\
                [c for c in dist_cc if c.replace('./', 'site/') not in [self.utils.replace_md(x) for x in site_cc]]
    
    def md2html(self, dist_path, src_path):
        with open(src_path, 'r') as f:
            html = markdown.markdown(f.read())
        
        with open(dist_path, 'w') as f:
            f.write(html)

    def convert(self):
        dist_content = self.compare_content()
        for content in dist_content:    
            dist_path = self.utils.replace_md(content.replace(f'{self.src_dir}/', ''))
            if os.path.isdir(content):
                os.mkdir(dist_path)

            elif not os.path.isdir(content) and os.path.isdir(dist_path): 
                shutil.rmtree(dist_path)

            elif os.path.isfile(content):
                self.md2html(dist_path+'.html', content)

            elif not os.path.isdir(content) and os.path.isfile(dist_path+'.html'): 
                os.remove(dist_path+'.html')

if __name__ == '__main__':
    convert = Convert()
    convert.convert()