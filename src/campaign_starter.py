"""選択課題を独立して開始するための、共通活動の到達例。"""
from library_hiroba import ui


def campaign_submit(app, pass_number, confirmation_code, photo):
    record = next((p for p in app.data["passes"] if p["number"] == pass_number.strip()), None)
    if record is None:
        return ui.alert("この観光パス番号は登録されていません。", kind="warning")
    if record["used"]:
        return ui.alert("この観光パスは応募済みです。", kind="warning")
    if photo not in app.data["photos"]:
        return ui.alert("写真を選んでください。", kind="warning")
    app.entries.append({"pass_number": pass_number.strip(), "photo": photo})
    if app.bugs:
        for item in app.data["passes"]:
            item["used"] = True
    else:
        record["used"] = True
    return ui.stack(ui.alert("応募を受け付けました。抽選結果は後日お知らせします。", kind="success"),
                    app.photo_preview(photo))


def campaign_form(app):
    return ui.form(lambda pass_number, confirmation_code, photo:
                   campaign_submit(app, pass_number, confirmation_code, photo),
        ui.field("pass_number", "観光パス番号（表面・6桁）", default="314159"),
        ui.field("confirmation_code", "応募確認コード（裏面）"),
        ui.field("photo", "投稿する写真", kind="choice", choices=app.photo_keys),
        title="まついわ よりみちキャンペーン", submit_label="写真を送って応募", clear_on_submit=False)
