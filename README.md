# 脑机交互长期试点

项目按来源版本保存业务资料，在 enrollment、sessions、followup 之上扩展了试点记录链：会话、校准版本、任务完成情况与人工辅助记录相互关联，按实际可用时间比较各试用阶段的独立完成率，衡量用户能否持续完成沟通任务，而非单次演示分数。

## 资料种类

- `participant`：入组人员，payload 含 `stage`、`enrolled_on`。
- `plan`：阶段计划，`stage` + `planned_sessions`（每人应完成的会话数，构成分母）。
- `session`：会话，`person`、`minutes`、`completed`。
- `calibration`：会话所用校准版本与判定，`session`、`version`、`valid`；研究人员提交新 revision 即可改判，旧判定仍保留。
- `assistance`：人工辅助记录，`session`、`actor`、`minutes`；`actor=caregiver` 即照护者代操作，其时长计入不可用原因 `caregiver_proxy`。
- `unavailability`：不可用时段，`session`、`reason`（`calibration`/`fatigue`/`device_down`）、`minutes`。
- `withdrawal`：中途退出，`person`、`reason`、`effective_on`；退出者仍留在分母中。
- `retraction`：撤回无效记录，`target_kind`、`target_id`、`reason`；只影响 `received_at` 之后的判定，此前报告不变。
- `report`：生成的阶段报告，作为不可覆盖版本保存，同一 revision 内容冲突会被拒绝。

## 指标

逐会话判定独立：任务完成、校准有效且无任何人工辅助。阶段汇总包括：

- `planned_sessions` = 入组人数 × 计划会话数（退出者不剔除）；
- `independent_rate` = 独立完成的会话 / 计划会话数；
- `usable_minutes` = 会话时长减去校准、疲劳、设备停用与照护者代操作时段；
- `independent_per_usable_hour` 按实际可用时间归一，供跨阶段比较；
- `unavailable_minutes` 按原因分列。

## 报告

`report.generate` 生成报告时与上一份保留报告对比，`changes` 中标出各阶段指标变化和可比较人群变化（新增/撤回人员、新退出者、计入/撤回的会话、因校准改判而独立性变化的会话），供产品团队决定后续试点范围。

运行与检查：

    python -m unittest discover -s tests -v
    python -m compileall -q neuro_trial tests
    python -m neuro_trial.cli data/example.json                      # 原有阶段汇总
    python -m neuro_trial.cli data/example.json --db pilot.db --report r1
    python -m neuro_trial.cli data/revised.json --db pilot.db --report r2
    python -m neuro_trial.cli data/revised.json --db pilot.db --list-reports

`data/revised.json` 演示研究人员改判校准（CAL-S4 无效）并撤回一段无效会话（S5）后的第二份报告；`--db` 使用文件路径时报告跨次保留。
