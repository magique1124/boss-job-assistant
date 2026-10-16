#!/usr/bin/env python3
"""维护投递追踪表：add 追加一行，update 按 JD 链接定位并更新列。

用法:
  python3 update_tracker.py <表.xlsx> add --company X --position Y [--salary S]
      [--jd URL] [--status 已投递] [--note N] [--interview I] [--replied 是] [--invited 是]
  python3 update_tracker.py <表.xlsx> update --jd URL --set 列名=值 [--set 列名=值 ...]

add 缺 --jd 时会用公司+岗位组合查重：已存在则更新该行而非新增。
"""
import argparse
import datetime
import sys

from openpyxl import load_workbook

COLUMNS = [
    "序号", "公司", "岗位", "薪资", "JD 链接",
    "是否投递", "是否回复", "是否约面", "面试情况", "备注", "更新时间",
]

ADD_FIELD_TO_COLUMN = {
    "company": "公司",
    "position": "岗位",
    "salary": "薪资",
    "jd": "JD 链接",
    "status": "是否投递",
    "replied": "是否回复",
    "invited": "是否约面",
    "interview": "面试情况",
    "note": "备注",
}


def fail(msg: str) -> int:
    print(f"ERROR: {msg}")
    return 1


def col_index(ws, name: str) -> int:
    for cell in ws[1]:
        if cell.value == name:
            return cell.column
    return 0


def today() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")


def find_row(ws, jd: str):
    jd_col = col_index(ws, "JD 链接")
    company_col = col_index(ws, "公司")
    position_col = col_index(ws, "岗位")
    for row in range(2, ws.max_row + 1):
        if jd and ws.cell(row=row, column=jd_col).value == jd:
            return row
    return None


def set_cell(ws, row: int, column_name: str, value: str) -> None:
    idx = col_index(ws, column_name)
    if not idx:
        raise KeyError(f"表中不存在列: {column_name}")
    ws.cell(row=row, column=idx, value=value)


def cmd_add(ws, args) -> int:
    if not args.company or not args.position:
        return fail("add 需要 --company 和 --position")
    row = find_row(ws, args.jd or "")
    if row is None:
        row = ws.max_row + 1
        seq_col = col_index(ws, "序号")
        prev = ws.cell(row=row - 1, column=seq_col).value if row > 2 else 0
        try:
            seq = int(prev or 0) + 1
        except (TypeError, ValueError):
            seq = row - 1
        ws.cell(row=row, column=seq_col, value=seq)
    for field, column in ADD_FIELD_TO_COLUMN.items():
        value = getattr(args, field, None)
        if value is not None:
            set_cell(ws, row, column, value)
    set_cell(ws, row, "更新时间", today())
    print(f"OK: 第 {row} 行 -> {args.company} / {args.position}")
    return 0


def cmd_update(ws, args) -> int:
    if not args.jd:
        return fail("update 需要 --jd 定位岗位")
    row = find_row(ws, args.jd)
    if row is None:
        return fail(f"未找到 JD 链接对应的行: {args.jd}")
    for pair in args.set or []:
        if "=" not in pair:
            return fail(f"--set 格式应为 列名=值: {pair}")
        name, value = pair.split("=", 1)
        name = name.strip()
        if name not in COLUMNS:
            return fail(f"无效列名: {name}（可选: {'/'.join(COLUMNS)}）")
        set_cell(ws, row, name, value.strip())
    set_cell(ws, row, "更新时间", today())
    print(f"OK: 第 {row} 行已更新")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="投递追踪表维护")
    parser.add_argument("file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("--company")
    p_add.add_argument("--position")
    p_add.add_argument("--salary")
    p_add.add_argument("--jd")
    p_add.add_argument("--status")
    p_add.add_argument("--replied")
    p_add.add_argument("--invited")
    p_add.add_argument("--interview")
    p_add.add_argument("--note")

    p_update = sub.add_parser("update")
    p_update.add_argument("--jd", required=True)
    p_update.add_argument("--set", action="append")

    args = parser.parse_args()

    try:
        wb = load_workbook(args.file)
    except Exception as exc:  # noqa: BLE001
        return fail(f"无法打开表格（先用 create_tracker.py 创建）: {exc}")
    ws = wb.active

    if args.command == "add":
        rc = cmd_add(ws, args)
    else:
        rc = cmd_update(ws, args)
    if rc == 0:
        wb.save(args.file)
    return rc


if __name__ == "__main__":
    sys.exit(main())
