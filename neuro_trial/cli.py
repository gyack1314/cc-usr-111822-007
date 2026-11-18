"""读取业务样例并展示当前结果。"""
import argparse
import json
from pathlib import Path
from .evidence import connect, receive
from .followup import stages
from .report import generate, reports
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('--db',default=':memory:',help='资料库路径，默认内存；用文件路径可跨次保留报告')
    parser.add_argument('--report',metavar='REVISION',help='生成该版本号的阶段报告并保存')
    parser.add_argument('--list-reports',action='store_true',help='列出所有保留的阶段报告')
    args=parser.parse_args()
    data=json.loads(Path(args.input).read_text(encoding='utf-8'))
    db=connect(args.db)
    for item in data['documents']:receive(db,item)
    if args.list_reports:
        print(json.dumps(reports(db),ensure_ascii=False,indent=2))
    elif args.report:
        print(json.dumps(generate(db,data['known_at'],args.report),ensure_ascii=False,indent=2))
    else:
        print(json.dumps(stages(db,data['known_at']),ensure_ascii=False,indent=2))
    db.close()
if __name__=='__main__':main()
