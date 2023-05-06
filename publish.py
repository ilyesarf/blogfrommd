import os, shutil
import markdown
from collections.abc import Iterable
import calendar
from datetime import datetime

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

        self.filter_dir = lambda d: self.src_dir not in d and '.' not in d
        self.filter_file = lambda f: f[0] != '.' and any(ext in f for ext in ['html', 'md', 'markdown'])
    
    def get_dist_cc(self):
        dist_cc = []
        for subdir, dirs, files in os.walk(self.dist_dir):
            if self.filter_dir(subdir[2:]):
                dist_cc.extend(self.utils.flatten([subdir+'/'+d for d in list(filter(self.filter_dir, dirs))] + [os.path.join(subdir, os.path.splitext(f)[0]) for f in list(filter(self.filter_file, files))]))     
        
        return dist_cc

    def compare_content(self):
        
        site_cc = self.utils.flatten([[subdir+'/'+d for d in list(filter(lambda d: '.' not in d, dirs))] + [os.path.join(subdir, f) for f in files] for subdir, dirs, files in os.walk(self.src_dir)])

        dist_cc = self.get_dist_cc() #current content
                
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

class Publish:
    def __init__(self, src_dir="site", dist_dir=".", posts_dir="bible/posts/"):
        self.src_dir = src_dir
        self.dist_dir = dist_dir
        self.posts_dir = posts_dir
        
        self.convert = Convert(src_dir, dist_dir)
        self.convert.convert()

    
    def md_info(self, filename="2022-03-22-who-am-i"): #extract article title and date and turn them into markdown
        parts = filename.split('-')

        date = f"{calendar.month_name[int(parts[1])]} {parts[2]}, {parts[0]}" 
        name = " ".join([w.capitalize() for w in parts[3:]])
        link = os.path.join(self.posts_dir, filename+".html")

        md = f'<span style="font-size: 14px; color: #828282;"> *{date}*</span>\n###[{name}](/{link})\n<br/>\n'
        return md
    
    def sort_posts(self):
        sorted_posts = os.listdir(self.posts_dir)

        sorted_posts.sort(key=lambda x: datetime.strptime('-'.join(x.split('-',3)[:3]), "%Y-%m-%d"))
        return sorted_posts


    def update_feed(self, feed_file=f"bible/index.html"):
        sorted_posts = self.sort_posts()

        html = ''
        for file in reversed(sorted_posts):
            info = self.md_info(self.convert.utils.replace_md(file))
            html += markdown.markdown(info)
            
        with open(feed_file, 'w') as f:
            f.write(html)

    
        
if __name__ == '__main__':
    convert = Publish()
    convert.update_feed()