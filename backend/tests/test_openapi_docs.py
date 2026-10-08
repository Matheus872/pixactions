def _resolve(spec: dict, schema: dict) -> dict:
    if "$ref" in schema:
        return spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
    if schema.get("type") == "array":
        return _resolve(spec, schema["items"])
    if "anyOf" in schema:
        return _resolve(spec, next(s for s in schema["anyOf"] if s.get("type") != "null"))
    return schema


def test_every_operation_is_documented(app):
    spec = app.openapi()
    problems = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            where = f"{method.upper()} {path}"
            for field in ("summary", "description", "tags"):
                if not op.get(field):
                    problems.append(f"{where}: missing {field}")
            ok = next((code for code in op["responses"] if code.startswith("2")), None)
            content = (op["responses"].get(ok) or {}).get("content", {}).get("application/json")
            if content is None:
                problems.append(f"{where}: no JSON success response")
            elif "examples" not in _resolve(spec, content["schema"]):
                problems.append(f"{where}: success schema has no examples")
            if op.get("security") and "401" not in op["responses"]:
                problems.append(f"{where}: authenticated route does not document 401")
    assert not problems, "\n".join(problems)
