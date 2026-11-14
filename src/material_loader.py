# GitHubから保存したZIPを、Colab／PyHirobaへ読み込みます。
import io
import json
import zipfile
from google.colab import files


def load_material_bundle(material_json):
    bundle = json.loads(material_json)
    if not isinstance(bundle, dict) or bundle.get("format") != "matsuiwa-materials-v0":
        raise ValueError("第4章4コマの教材のZIPを選んでください。")
    case = bundle["case"]
    app_source = bundle["app_source"]
    feature_source = bundle["feature_source"]
    if not isinstance(case, dict) or not all(isinstance(value, str) for value in (app_source, feature_source)):
        raise ValueError("教材データの形式を確認してください。")
    globals().update(CASE=case, APP_SOURCE=app_source, FEATURE_SOURCE=feature_source)
    return ui.alert("教材データを読み込みました。次のセルへ進んでください。", kind="success")


def start_task(task="start"):
    if "CASE" not in globals():
        raise RuntimeError("先に読込セルを実行し、GitHubから保存したZIPを選んでください。")
    exec(APP_SOURCE, globals())
    exec(FEATURE_SOURCE, globals())
    return new_case(task)


print("GitHubから保存したZIP（ch04-04-materials-main.zip）を1つ選んでください。")
uploaded_materials = files.upload()
if not uploaded_materials:
    material_result = ui.alert("ファイルが選ばれていません。もう一度このセルを実行してください。", kind="warning")
else:
    candidates = []
    for filename, content in uploaded_materials.items():
        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = [name for name in archive.namelist()
                         if name.replace("\\", "/").endswith("data/runtime_bundle.json")]
                if len(names) != 1:
                    raise ValueError("第4章4コマの教材のZIPを選んでください。")
                # 必要なJSONだけを読みます。ZIP内のプログラムをファイルとして展開しません。
                candidates.append(archive.read(names[0]).decode("utf-8-sig"))
        elif filename.endswith("runtime_bundle.json"):
            candidates.append(bytes(content).decode("utf-8-sig"))
    if len(candidates) != 1:
        raise ValueError("GitHubから保存したZIPを1つだけ選んでください。")
    material_result = load_material_bundle(candidates[0])
material_result
