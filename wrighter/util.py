def wrighter_loguru_formater(record: dict) -> str:
    def color_tag(text: str, c: str):
        return f"<{c}>{text}</{c}>"

    time = color_tag("{time:YYYY-MM-DD HH:mm:ss.SSS}", "light-black")
    level = color_tag("{level: <8}", "level")
    msg = color_tag("{message:<24}", "level")
    name = color_tag("{name}", "light-blue")
    func = color_tag("{function}", "light-blue")
    lineno = color_tag("{line}", "light-blue")
    plugin = color_tag("{plugin}", "green-blue")

    extras = ""
    if len(record["extra"]):
        for key in record["extra"].keys():
            if key == "plugin":
                continue
            extras = extras + key + "=" + "{extra[" + key + "]}, "
        extras = extras[:-2]

    if "plugin" in record["extra"]:
        fmt = f"{time} [ {level} ] [ {plugin} ] {name}:{func}:{lineno} - {msg} {extras}\n"
    else:
        fmt = f"{time} [ {level} ] {name}:{func}:{lineno} - {msg} {extras}\n"
    return fmt


__all__ = ["wrighter_loguru_formater"]
