import os, shutil
import markdown
import calendar
import argparse
import yaml
from collections.abc import Iterable
from datetime import datetime
from hashlib import md5

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

class Config:
    def __init__(self, conf_file):
        self.conf = yaml.safe_load(open(conf_file, 'r'))

    def get_style(self):
        style = self.conf["style"]
        supported_conf = {"font": "", "bg-color": "\"\""}
        if style:
            for k in style.keys():
                if k in supported_conf.keys():
                    supported_conf[k] = style[k]
                else:
                    print(f"{k} is not supported yet")

        style_html = f"\n<style> body {{font-family: {supported_conf['font']};background-color: {supported_conf['bg-color']}}}</style>\n"
        
        return style_html
    
    def apply_style(self, files):
        for file in files:
            with open(file, 'r') as f:
                style_html = self.get_style()
                content = f.readlines()
                if content[-1].strip() != style_html.strip():           
                    content[-1] = style_html
                    open(file, 'w').write("".join(content))
        
class Convert:
    def __init__(self, src_dir, dist_dir, tool_dir, conf_file):
        self.utils = Utils
        if os.path.isfile(conf_file):
            self.config = Config(conf_file)

        self.src_dir = src_dir
        self.dist_dir = dist_dir

        self.filter_dir = lambda d: self.src_dir != d.split('/')[0] and '.' not in d and d != os.path.basename(os.getcwd()) and tool_dir != os.path.basename(d)
        self.filter_file = lambda f: f[0] != '.' and any(ext in f for ext in ['html', 'md', 'markdown'])
    
    def get_dist_cc(self):
        dist_cc = []
        for subdir, dirs, files in os.walk(self.dist_dir):
            if self.filter_dir(subdir[2:]):
                dist_cc.extend(self.utils.flatten([subdir+'/'+d for d in list(filter(self.filter_dir, dirs))] + [os.path.join(subdir, os.path.splitext(f)[0]) for f in list(filter(self.filter_file, files))]))     
        
        return dist_cc
    
    def compare_chsum(self, src_file, dist_file):
        is_same = True
        if all([os.path.isfile(f) for f in [src_file, dist_file]]):
            html_src_f = markdown.markdown(open(src_file, 'r').read()).encode()
            html_dist_f = open(dist_file, 'rb').read()

            is_same = md5(html_src_f).hexdigest() == md5(html_dist_f).hexdigest() 

        return is_same
        
    def compare_content(self):        
        site_cc = self.utils.flatten([[subdir+'/'+d for d in list(filter(lambda d: '.' not in d, dirs))] + [os.path.join(subdir, f) for f in files] for subdir, dirs, files in os.walk(self.src_dir)])
        self.config.apply_style([file for file in site_cc if os.path.isfile(file)])

        dist_cc = self.get_dist_cc() #current content
        
        return [c for c in site_cc if self.utils.replace_md(c.replace(f'{self.src_dir}/', f'{self.dist_dir}/')) not in dist_cc\
                or self.compare_chsum(c, self.utils.replace_md(c.replace(f'{self.src_dir}/',f'{self.dist_dir}/'))+'.html') == False] +\
                [c for c in dist_cc if c.replace(f'{self.dist_dir}/', f'{self.src_dir}/') not in [self.utils.replace_md(x) for x in site_cc]]
    
    def md2html(self, dist_path, src_path):
        with open(src_path, 'r') as f:
            html = markdown.markdown(f.read())
        
        with open(dist_path, 'w') as f:
            f.write(html)

    def convert(self):
        dist_content = self.compare_content()

        for content in dist_content:    
            dist_path = self.utils.replace_md(content.replace(f'{self.src_dir}/', f'{self.dist_dir}/'))
            if os.path.isdir(content):
                os.mkdir(dist_path)

            elif not os.path.isdir(content) and os.path.isdir(dist_path): 
                shutil.rmtree(dist_path)

            elif os.path.isfile(content):
                self.md2html(dist_path+'.html', content)

            elif not os.path.isdir(content) and os.path.isfile(dist_path+'.html'): 
                os.remove(dist_path+'.html')

class Publish:
    def __init__(self, conf_file, tool_dir, src_dir, dist_dir, posts_dir):
        self.src_dir = src_dir
        self.dist_dir = dist_dir
        if not os.path.isdir(self.dist_dir) and self.dist_dir != ".":
            os.mkdir(self.dist_dir)

        self.posts_dir = posts_dir
        
        self.convert = Convert(src_dir, dist_dir, tool_dir, conf_file)
        self.update_feed()
        self.convert.convert()

    
    def md_info(self, filename): #extract article title and date and turn them into markdown
        parts = filename.split('-')

        date = f"{calendar.month_name[int(parts[1])]} {parts[2]}, {parts[0]}" 
        name = " ".join([w.capitalize() for w in parts[3:]])
        link = os.path.join(self.posts_dir, filename+".html")

        md = f'<span style="font-size: 14px; color: #828282;"> *{date}*</span>\n###[{name}](/{link})\n<br/>\n'
        return md
    
    def sort_posts(self):
        sorted_posts = os.listdir(f"{self.src_dir}/{self.posts_dir}")

        sorted_posts.sort(key=lambda x: datetime.strptime('-'.join(x.split('-',3)[:3]), "%Y-%m-%d"))
        return sorted_posts


    def update_feed(self, feed_file="bible/index.markdown"):
        feed_file = os.path.join(self.src_dir, feed_file)
        sorted_posts = self.sort_posts()

        md = ''
        for file in reversed(sorted_posts):
            info = self.md_info(self.convert.utils.replace_md(file))
            md += info
            
        with open(feed_file, 'w') as f:
            f.write(md)

    @staticmethod
    def serve(port=8000):
        import http.server
        import socketserver

        Handler = http.server.SimpleHTTPRequestHandler

        with socketserver.TCPServer(("", port), Handler) as httpd:
            print("serving at port", port)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("Shutting down server...")
                httpd.shutdown()
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="blogfrommd manual")

    parser.add_argument('--conf_file', default='conf.yml', help='Specify the config file path')

    parser.add_argument('--tool_dir', default='blogfrommd', help='Specify the blogfrommd directory (only when you\'re running it outside the directory)')
    parser.add_argument('--src_dir', default='site', help='Specify the source directory')

    parser.add_argument('--dist_dir', default='.', help='Specify the destination directory')

    parser.add_argument('--posts_dir', default='bible/posts', help='Specify the posts directory')
    parser.add_argument('--serve', action='store_true', help='Enable serving the application')

    args = parser.parse_args()

    #remove / in the ending of a directory name
    for arg in vars(args):
        if 'dir' in arg:
            if vars(args)[arg][-1] == '/':
                vars(args)[arg] = vars(args)[arg][:-1]
                
    publish = Publish(conf_file=args.conf_file, tool_dir=args.tool_dir, src_dir=args.src_dir, dist_dir=args.dist_dir, posts_dir=args.posts_dir)
    
    if args.serve:
        publish.serve()