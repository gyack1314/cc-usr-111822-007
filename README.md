# 脑机交互长期试点

项目按来源版本保存业务资料，已有 enrollment、sessions、followup 环节。现有入组、会话和阶段结果只汇总观察到的使用，尚未处理退出、校准更正和人工辅助对长期独立完成的影响。

运行与检查：

    python -m unittest discover -s tests -v
    python -m compileall -q neuro_trial tests
    python -m neuro_trial.cli data/example.json
