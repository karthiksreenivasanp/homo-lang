class Lexer:
    def tokenize(self, source):
        lines = source.splitlines()
        tokens = []
        i = 0


        def _split_csv(text):
            return [t.strip() for t in text.split(",") if t.strip()]

        def _parse_kv_options(text):
            opts = {}
            if not text:
                return opts
            for item in _split_csv(text):
                if "=" in item:
                    k, v = item.split("=", 1)
                elif ":" in item:
                    k, v = item.split(":", 1)
                else:
                    opts[item.strip()] = True
                    continue
                opts[k.strip()] = v.strip()
            return opts

        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("#"):
                i += 1
                continue

            # ── Modules / imports ─────────────────────────────────────────────
            if line.startswith("use "):
                tokens.append(("USE", line[4:].strip()))

            # ── Networking ────────────────────────────────────────────────────
            elif line.startswith("visit "):
                tokens.append(("VISIT", line[6:].strip()))
            elif line.startswith("fetch ") and " as " in line:
                parts = line[6:].split(" as ", 1)
                tokens.append(("FETCH", parts[0].strip(), parts[1].strip()))
            elif line.startswith("post ") and " to " in line:
                rest = line[5:]
                parts = rest.split(" to ", 1)
                data = parts[0].strip()
                right = parts[1].strip()
                if " as " in right:
                    url_part, var = right.split(" as ", 1)
                    tokens.append(("POST", data, url_part.strip(), var.strip()))
                else:
                    tokens.append(("POST", data, right, "_response"))
            elif line.startswith("connect socket "):
                tokens.append(("CONNECT_SOCKET", line[15:].strip()))
            elif line.startswith("send socket "):
                tokens.append(("SEND_SOCKET", line[12:].strip()))
            elif line.startswith("serve on port "):
                tokens.append(("SERVE", line[14:].strip()))
            elif line == "serve":
                tokens.append(("SERVE", "8080"))

            # ── Database ──────────────────────────────────────────────────────
            elif line.startswith("open database "):
                tokens.append(("OPEN_DB", line[14:].strip()))
            elif line.startswith("connect database "):
                rest = line[17:].strip()
                if " at " in rest:
                    db_type, url = rest.split(" at ", 1)
                    tokens.append(("CONNECT_DB", db_type.strip(), url.strip()))
                else:
                    tokens.append(("CONNECT_DB", rest, ""))
            elif line.startswith("query ") and " where " in line and " as " in line:
                rest = line[6:]
                tbl, right = rest.split(" where ", 1)
                cond, var = right.split(" as ", 1)
                tokens.append(("QUERY_DB", tbl.strip(), cond.strip(), var.strip()))
            elif line.startswith("delete ") and " from database" in line:
                key = line[7:line.index(" from database")].strip()
                tokens.append(("DELETE_DB", key))
            elif line.startswith("set ") and line.endswith(" as table"):
                tokens.append(("CREATE_TABLE", line[4:-9].strip()))
            elif line.startswith("print table "):
                tokens.append(("PRINT_TABLE", line[12:].strip()))

            # ── Check / assert ────────────────────────────────────────────────
            elif line.startswith("check ") and " is " in line:
                parts = line[6:].split(" is ")
                tokens.append(("CHECK", parts[0].strip(), parts[1].strip()))
            elif line.startswith("assert ") and " otherwise " in line:
                parts = line[7:].split(" otherwise ", 1)
                tokens.append(("ASSERT", parts[0].strip(), parts[1].strip()))

            # ── Environment ───────────────────────────────────────────────────
            elif line.startswith("set env ") and " as " in line:
                rest = line[8:]
                k, v = rest.split(" as ", 1)
                tokens.append(("SET_ENV", k.strip(), v.strip()))
            elif line.startswith("get env ") and " as " in line:
                rest = line[8:]
                k, v = rest.split(" as ", 1)
                tokens.append(("GET_ENV", k.strip(), v.strip()))

            # ── Logging / sleep / run ─────────────────────────────────────────
            elif line.startswith("log "):
                tokens.append(("LOG", line[4:].strip()))
            elif line.startswith("sleep "):
                tokens.append(("SLEEP", line[6:].strip()))
            elif line.startswith("run "):
                tokens.append(("RUN", line[4:].strip()))

            # ── Auth ──────────────────────────────────────────────────────────
            elif line.startswith("login with "):
                tokens.append(("LOGIN", line[11:].strip()))
            elif line == "logout":
                tokens.append(("LOGOUT",))

            # ── Email ─────────────────────────────────────────────────────────
            elif line.startswith("send email to "):
                rest = line[14:]
                to = rest.split(" with subject ")[0].strip()
                body_part = rest.split(" with subject ", 1)[1] if " with subject " in rest else ""
                if " and body " in body_part:
                    subj, bdy = body_part.split(" and body ", 1)
                else:
                    subj, bdy = body_part, ""
                tokens.append(("SEND_EMAIL", to, subj.strip(), bdy.strip()))

            # ── PDF / Image export ────────────────────────────────────────────
            elif line.startswith("export pdf as "):
                tokens.append(("EXPORT_PDF", line[14:].strip()))
            elif line.startswith("resize image ") and " to " in line and " by " in line:
                rest = line[13:]
                file_part, dims = rest.split(" to ", 1)
                w, h = dims.split(" by ", 1)
                tokens.append(("RESIZE_IMAGE", file_part.strip(), w.strip(), h.strip()))
            elif line.startswith("export "):
                tokens.append(("EXPORT", line[7:].strip()))

            # ── Crypto / security ─────────────────────────────────────────────
            elif line.startswith("hash ") and " as " in line:
                parts = line[5:].split(" as ", 1)
                tokens.append(("HASH", parts[0].strip(), parts[1].strip()))
            elif line.startswith("encrypt ") and " with " in line:
                parts = line[8:].split(" with ", 1)
                value_part = parts[0].strip()
                key_and_result = parts[1].strip()
                if " as " in key_and_result:
                    key_part, result_var = key_and_result.split(" as ", 1)
                    tokens.append(("ENCRYPT", value_part, key_part.strip(), result_var.strip()))
                else:
                    tokens.append(("ENCRYPT", value_part, key_and_result, "result"))
            elif line.startswith("decrypt ") and " with " in line:
                parts = line[8:].split(" with ", 1)
                value_part = parts[0].strip()
                key_and_result = parts[1].strip()
                if " as " in key_and_result:
                    key_part, result_var = key_and_result.split(" as ", 1)
                    tokens.append(("DECRYPT", value_part, key_part.strip(), result_var.strip()))
                else:
                    tokens.append(("DECRYPT", value_part, key_and_result, "result"))

            # ── File system ───────────────────────────────────────────────────
            elif line.startswith("delete file "):
                tokens.append(("DELETE_FILE", line[12:].strip()))
            elif line.startswith("make folder "):
                tokens.append(("MAKE_DIR", line[12:].strip()))
            elif line.startswith("list files in ") and " as " in line:
                parts = line[14:].split(" as ", 1)
                tokens.append(("LIST_FILES", parts[0].strip(), parts[1].strip()))
            elif line.startswith("copy ") and " as " in line:
                parts = line[5:].split(" as ", 1)
                tokens.append(("COPY", parts[0].strip(), parts[1].strip()))

            # ── List helpers ──────────────────────────────────────────────────
            elif line.startswith("append ") and " to " in line:
                parts = line[7:].split(" to ", 1)
                tokens.append(("APPEND", parts[0].strip(), parts[1].strip()))
            elif line.startswith("remove ") and " from " in line:
                parts = line[7:].split(" from ", 1)
                tokens.append(("REMOVE", parts[0].strip(), parts[1].strip()))
            elif line.startswith("count ") and " in " in line and " as " in line:
                rest = line[6:]
                value, right = rest.split(" in ", 1)
                lst, result = right.split(" as ", 1)

                tokens.append((
                    "COUNT",
                    value.strip(),
                    lst.strip(),
                    result.strip()
                ))
            elif line.startswith("sort ") and line.endswith(" descending"):
                tokens.append(("SORT", line[5:-11].strip(), True))
            elif line.startswith("sort "):
                tokens.append(("SORT", line[5:].strip(), False))
            elif line.startswith("reverse "):

                rest = line[8:].strip()

                if " as " in rest:

                    source, target = rest.split(" as ", 1)

                    tokens.append(
                        ("REVERSE", source.strip(), target.strip())
                    )

                else:

                    tokens.append(
                        ("REVERSE", rest.strip(), "reversed")
                    )
            elif line.startswith("filter ") and " where " in line and " as " in line:
                rest = line[7:]
                var, right = rest.split(" where ", 1)
                cond, res = right.split(" as ", 1)
                tokens.append(("FILTER", var.strip(), cond.strip(), res.strip()))
            elif line.startswith("map ") and " with " in line and " as " in line:
                rest = line[4:]
                var, right = rest.split(" with ", 1)
                expr, res = right.split(" as ", 1)
                tokens.append(("MAP", var.strip(), expr.strip(), res.strip()))
            elif line.startswith("join ") and " with " in line and " as " in line:
                rest = line[5:]
                lst, right = rest.split(" with ", 1)
                sep, var = right.split(" as ", 1)
                tokens.append(("JOIN", lst.strip(), sep.strip().strip('"\''), var.strip()))
            elif line.startswith("split ") and " by " in line and " as " in line:
                rest = line[6:]
                var, right = rest.split(" by ", 1)
                sep, res = right.split(" as ", 1)
                tokens.append(("SPLIT", var.strip(), sep.strip().strip('"\''), res.strip()))

            # ── Class / object ────────────────────────────────────────────────
            elif line.startswith("inherit ") and " from " in line:
                parts = line[8:].split(" from ")
                tokens.append(("INHERIT_CLASS", parts[0].strip(), parts[1].strip()))

            # ── Background tasks ──────────────────────────────────────────────
            elif line.startswith("start ") and "=" not in line:
                tokens.append(("TASK", line[6:].strip()))

            # ── Charts ────────────────────────────────────────────────────────
            elif line.startswith("show chart ") and " of " in line:
                rest = line[11:]
                chart_type, var = rest.split(" of ", 1)
                tokens.append(("SHOW_CHART", chart_type.strip(), var.strip()))
            elif line.startswith("show chart of "):
                tokens.append(("MEDIA", "chart", line[14:].strip()))


            # ── Media ─────────────────────────────────────────────────────────
            elif line.startswith("open picture "):
                tokens.append(("MEDIA", "open", line[13:].strip()))
            elif line == "show picture":
                tokens.append(("MEDIA", "show", "picture"))
            elif line.startswith("play music "):
                tokens.append(("MEDIA", "play_music", line[11:].strip()))
            elif line.startswith("play video "):
                tokens.append(("MEDIA", "play_video", line[11:].strip()))

            # ── Data science ───────────────────────────────────────────────────
            elif line.startswith("load data ") and " as " in line:
                rest = line[10:]
                src, right = rest.split(" as ", 1)
                opts = {}
                if " with " in right:
                    var, opt_raw = right.split(" with ", 1)
                    opts = _parse_kv_options(opt_raw)
                else:
                    var = right
                tokens.append(("LOAD_DATA", src.strip(), var.strip(), opts))
            elif line.startswith("save data ") and " as " in line:
                rest = line[10:]
                var, right = rest.split(" as ", 1)
                opts = {}
                if " with " in right:
                    file_part, opt_raw = right.split(" with ", 1)
                    opts = _parse_kv_options(opt_raw)
                else:
                    file_part = right
                tokens.append(("SAVE_DATA", var.strip(), file_part.strip(), opts))
            elif line.startswith("show data "):
                rest = line[10:].strip()
                if " rows" in rest:
                    var, rows = rest.split(" rows", 1)
                    var = var.strip()
                    # extract the number before " rows"
                    # "df 3" -> "df", "3"
                    parts = var.rsplit(" ", 1)
                    if len(parts) == 2:
                        var = parts[0]
                        rows_val = parts[1]
                    else:
                        rows_val = "5"
                    tokens.append(("SHOW_DATA", var.strip(), rows_val.strip()))
                else:
                    tokens.append(("SHOW_DATA", rest))
            elif line.startswith("describe data "):
                tokens.append(("DESCRIBE_DATA", line[14:].strip()))
            elif line.startswith("select columns ") and " from " in line and " as " in line:
                rest = line[15:]
                cols_part, right = rest.split(" from ", 1)
                df_part, res = right.split(" as ", 1)
                tokens.append(("SELECT_COLS", _split_csv(cols_part), df_part.strip(), res.strip()))
            elif line.startswith("drop columns ") and " from " in line:
                rest = line[13:]
                cols_part, df_part = rest.split(" from ", 1)
                tokens.append(("DROP_COLS", _split_csv(cols_part), df_part.strip()))
            elif line.startswith("rename column ") and " to " in line and " in " in line:
                rest = line[14:]
                old, right = rest.split(" to ", 1)
                new, df_part = right.split(" in ", 1)
                tokens.append(("RENAME_COL", old.strip(), new.strip(), df_part.strip()))
            elif line.startswith("filter rows in ") and " where " in line and " as " in line:
                rest = line[15:]
                df_part, right = rest.split(" where ", 1)
                cond, res = right.split(" as ", 1)
                tokens.append(("FILTER_ROWS", df_part.strip(), cond.strip(), res.strip()))
            elif line.startswith("group ") and " by " in line and " then " in line and " as " in line:
                rest = line[6:]
                df_part, right = rest.split(" by ", 1)
                by_col, right = right.split(" then ", 1)
                agg_part, res = right.split(" as ", 1)
                agg_bits = agg_part.strip().split(" ", 1)
                agg_func = agg_bits[0]
                agg_col = agg_bits[1] if len(agg_bits) > 1 else by_col
                tokens.append(("GROUP_BY", df_part.strip(), by_col.strip(), agg_func.strip(), agg_col.strip(), res.strip()))
            elif line.startswith("merge ") and " with " in line and " on " in line and " as " in line:
                rest = line[6:]
                df1, right = rest.split(" with ", 1)
                df2, right = right.split(" on ", 1)
                how = "inner"
                if " how " in right and " as " in right:
                    on_part, right = right.split(" how ", 1)
                    how_part, res = right.split(" as ", 1)
                    on_key = on_part.strip()
                    how = how_part.strip()
                else:
                    on_key, res = right.split(" as ", 1)
                tokens.append(("MERGE_DATA", df1.strip(), df2.strip(), on_key.strip(), how, res.strip()))
            elif line.startswith("fill missing in ") and " with " in line:
                rest = line[16:]
                df_part, right = rest.split(" with ", 1)
                value = right
                col = None
                if " column " in right:
                    value, col = right.split(" column ", 1)
                tokens.append(("FILL_MISSING", df_part.strip(), value.strip(), col.strip() if col else None))
            elif line.startswith("drop missing in "):
                tokens.append(("DROP_MISSING", line[16:].strip()))
            elif line.startswith("add column ") and " to " in line and " as " in line:
                rest = line[11:]
                col, right = rest.split(" to ", 1)
                df_part, expr = right.split(" as ", 1)
                tokens.append(("ADD_COLUMN", col.strip(), df_part.strip(), expr.strip()))
            elif line.startswith("normalize "):
                rest = line[10:].strip()
                if rest.startswith("column ") and " in " in rest:
                    _, right = rest.split(" ", 1)
                    col, df_part = right.split(" in ", 1)
                    tokens.append(("NORMALIZE", df_part.strip(), col.strip()))
                elif " column " in rest:
                    df_part, col = rest.split(" column ", 1)
                    tokens.append(("NORMALIZE", df_part.strip(), col.strip()))
                else:
                    tokens.append(("NORMALIZE", rest))
            elif line.startswith("standardize "):
                rest = line[12:].strip()
                if rest.startswith("column ") and " in " in rest:
                    _, right = rest.split(" ", 1)
                    col, df_part = right.split(" in ", 1)
                    tokens.append(("STANDARDIZE", df_part.strip(), col.strip()))
                elif " column " in rest:
                    df_part, col = rest.split(" column ", 1)
                    tokens.append(("STANDARDIZE", df_part.strip(), col.strip()))
                else:
                    tokens.append(("STANDARDIZE", rest))
            elif line.startswith("encode ") and " column " in line:
                rest = line[7:]
                df_part, col = rest.split(" column ", 1)
                tokens.append(("ENCODE", df_part.strip(), col.strip()))
            elif line.startswith("split ") and " into train " in line and " test " in line:
                rest = line[6:]
                df_part, right = rest.split(" into train ", 1)
                train_var, right = right.split(" test ", 1)
                ratio = "0.8"
                target = None
                if " ratio " in right:
                    test_var, right = right.split(" ratio ", 1)
                    ratio = right.strip().split()[0]
                    remainder = right[len(ratio):].strip()
                    if remainder.startswith("target "):
                        target = remainder[7:].strip()
                else:
                    test_var = right
                tokens.append(("SPLIT_DATA", df_part.strip(), train_var.strip(), test_var.strip(), ratio, target))
            elif line.startswith("plot "):
                rest = line[5:].strip()
                chart_type = "line"
                title = ""
                x_col = None
                y_col = None
                save_as = None
                if " as " in rest:
                    var, right = rest.split(" as ", 1)
                    chart_bits = right.split()
                    chart_type = chart_bits[0]
                    right = " ".join(chart_bits[1:])
                else:
                    var, right = rest, ""
                if " title " in right:
                    right, title_part = right.split(" title ", 1)
                    title = title_part.strip().strip('"\'')
                if " x " in right:
                    right, x_part = right.split(" x ", 1)
                    x_col = x_part.strip().split()[0]
                    right = right.replace(x_col, "", 1).strip()
                if " y " in right:
                    right, y_part = right.split(" y ", 1)
                    y_col = y_part.strip().split()[0]
                    right = right.replace(y_col, "", 1).strip()
                if " save as " in right:
                    _, save_part = right.split(" save as ", 1)
                    save_as = save_part.strip().strip('"\'')
                tokens.append(("PLOT", var.strip(), chart_type, title, x_col, y_col, save_as))
            elif line.startswith("stats ") and " as " in line:
                rest = line[6:]
                var, res = rest.split(" as ", 1)
                tokens.append(("STATS", var.strip(), res.strip()))

            # ── Machine learning (Kid-Friendly Syntax) ────────────────────────
            elif line.startswith("make AI ") and " as " in line:
                rest = line[8:]
                model_type, right = rest.split(" as ", 1)
                params = {}
                if " with " in right:
                    name, opt_raw = right.split(" with ", 1)
                    params = _parse_kv_options(opt_raw)
                else:
                    name = right
                tokens.append(("CREATE_MODEL", model_type.strip().strip('"\''), name.strip(), params))

            elif line.startswith("teach ") and " using " in line and " to guess " in line:
                rest = line[6:]
                model, right = rest.split(" using ", 1)
                df_part, right = right.split(" to guess ", 1)
                target = right.strip().strip('"\'')
                features = None
                if " features " in right:
                    target, feat_part = right.split(" features ", 1)
                    features = _split_csv(feat_part)
                tokens.append(("TRAIN_MODEL", model.strip(), df_part.strip(), target.strip(), features))

            elif line.startswith("test ") and " on " in line and " as " in line:
                rest = line[5:]
                model, right = rest.split(" on ", 1)
                df_part, right = right.split(" as ", 1)
                result = right.strip()
                target = None
                metric = None
                if " predict " in right:
                    result, tpart = right.split(" predict ", 1)
                    target = tpart.strip().strip('"\'')
                if " metric " in right:
                    result, mpart = right.split(" metric ", 1)
                    metric = mpart.strip().strip('"\'')
                tokens.append(("EVALUATE_MODEL", model.strip(), df_part.strip(), result.strip(), target, metric))

            elif line.startswith("ask ") and " about " in line and " as " in line:
                rest = line[4:]
                model, right = rest.split(" about ", 1)
                source, res = right.split(" as ", 1)
                tokens.append(("PREDICT", model.strip(), source.strip(), res.strip()))
                
            elif line.startswith("learn from ") and " to guess " in line and " as " in line:
                rest = line[11:]
                df_part, right = rest.split(" to guess ", 1)
                target, right = right.split(" as ", 1)
                name = right.strip()
                tokens.append(("CREATE_MODEL", "forest", name, {}))
                tokens.append(("TRAIN_MODEL", name, df_part.strip(), target.strip().strip('"\''), None))
            elif line.startswith("save model ") and " as " in line:
                rest = line[11:]
                name, file_part = rest.split(" as ", 1)
                tokens.append(("SAVE_MODEL", name.strip(), file_part.strip()))
            elif line.startswith("load model ") and " as " in line:
                rest = line[11:]
                file_part, name = rest.split(" as ", 1)
                tokens.append(("LOAD_MODEL", file_part.strip(), name.strip()))
            elif line.startswith("upgrade ") and " times on " in line and " to guess " in line and " as " in line:
                rest = line[8:]
                model, right = rest.split(" ", 1)
                trials, right = right.split(" times on ", 1)
                df_part, right = right.split(" to guess ", 1)
                target, res = right.split(" as ", 1)
                tokens.append(("TUNE_MODEL", model.strip(), df_part.strip(), target.strip().strip('"\''), trials.strip(), res.strip()))
            elif line.startswith("check ") and " times on " in line and " to guess " in line and " as " in line:
                rest = line[6:]
                model, right = rest.split(" ", 1)
                folds, right = right.split(" times on ", 1)
                df_part, right = right.split(" to guess ", 1)
                target, res = right.split(" as ", 1)
                tokens.append(("CROSS_VALIDATE", model.strip(), df_part.strip(), target.strip().strip('"\''), folds.strip(), res.strip()))
            elif line.startswith("find clues in ") and " as " in line:
                rest = line[14:]
                model, res = rest.split(" as ", 1)
                tokens.append(("FEATURE_IMPORTANCE", model.strip(), res.strip()))
            elif line.startswith("confusion matrix of ") and " on " in line and " as " in line:
                rest = line[21:]
                model, right = rest.split(" on ", 1)
                df_part, res = right.split(" as ", 1)
                target = None
                if " target " in right:
                    df_part, tpart = right.split(" target ", 1)
                    target = tpart.strip()
                tokens.append(("CONFUSION_MATRIX", model.strip(), df_part.strip(), res.strip(), target))

            # ── Deep learning ──────────────────────────────────────────────────
            elif line.startswith("create network ") and " layers " in line:
                rest = line[15:]
                name, right = rest.split(" layers ", 1)
                layers_part = right
                activation = "relu"
                output_activation = None
                if " activation " in right:
                    layers_part, act_part = right.split(" activation ", 1)
                    activation = act_part.strip().split()[0]
                if " output activation " in right:
                    layers_part, out_part = right.split(" output activation ", 1)
                    output_activation = out_part.strip().split()[0]
                layers = [int(x.strip()) for x in _split_csv(layers_part)]
                tokens.append(("CREATE_NETWORK", name.strip(), layers, activation, output_activation))
            elif line.startswith("train network ") and " on " in line and " predict " in line:
                rest = line[14:]
                name, right = rest.split(" on ", 1)
                df_part, right = right.split(" predict ", 1)
                target = right.strip()
                epochs = batch = lr = loss = optimizer = features = None
                if " epochs " in right:
                    target, right = right.split(" epochs ", 1)
                    epochs = right.strip().split()[0]
                if " batch " in right:
                    right = right.split(" batch ", 1)[1]
                    batch = right.strip().split()[0]
                if " lr " in right:
                    right = right.split(" lr ", 1)[1]
                    lr = right.strip().split()[0]
                if " loss " in right:
                    right = right.split(" loss ", 1)[1]
                    loss = right.strip().split()[0]
                if " optimizer " in right:
                    right = right.split(" optimizer ", 1)[1]
                    optimizer = right.strip().split()[0]
                if " features " in right:
                    feat_part = right.split(" features ", 1)[1]
                    features = _split_csv(feat_part)
                tokens.append(("TRAIN_NETWORK", name.strip(), df_part.strip(), target.strip(),
                               epochs, batch, lr, loss, optimizer, features))
            elif line.startswith("predict network ") and " on " in line and " as " in line:
                rest = line[16:]
                name, right = rest.split(" on ", 1)
                source, res = right.split(" as ", 1)
                tokens.append(("PREDICT_NETWORK", name.strip(), source.strip(), res.strip()))
            elif line.startswith("save network ") and " as " in line:
                rest = line[13:]
                name, file_part = rest.split(" as ", 1)
                tokens.append(("SAVE_NETWORK", name.strip(), file_part.strip()))
            elif line.startswith("load network ") and " as " in line:
                rest = line[13:]
                file_part, name = rest.split(" as ", 1)
                tokens.append(("LOAD_NETWORK", file_part.strip(), name.strip()))
            elif line.startswith("set loss of ") and " as " in line:
                rest = line[12:]
                name, loss = rest.split(" as ", 1)
                tokens.append(("SET_LOSS", name.strip(), loss.strip()))
            elif line.startswith("set optimizer of ") and " as " in line:
                rest = line[17:]
                name, right = rest.split(" as ", 1)
                opt = right.strip().split()[0]
                lr = None
                if " lr " in right:
                    _, lr = right.split(" lr ", 1)
                tokens.append(("SET_OPTIMIZER", name.strip(), opt, lr.strip() if lr else None))

            # ── Local LLM ─────────────────────────────────────────────────────
            elif line.startswith("load llm ") and " as " in line:
                rest = line[9:]
                src, right = rest.split(" as ", 1)
                opts = {}
                if " with " in right:
                    var, opt_raw = right.split(" with ", 1)
                    opts = _parse_kv_options(opt_raw)
                else:
                    var = right
                tokens.append(("LOAD_LLM", src.strip(), var.strip(), opts))
            elif line.startswith("prompt ") and " with " in line and " as " in line:
                rest = line[7:]
                llm_var, right = rest.split(" with ", 1)
                prompt, res = right.split(" as ", 1)
                opts = {}
                if " with " in res:
                    res, opt_raw = res.split(" with ", 1)
                    opts = _parse_kv_options(opt_raw)
                tokens.append(("PROMPT_LLM", llm_var.strip(), prompt.strip(), res.strip(), opts))
            elif line.startswith("set llm param ") and " as " in line:
                rest = line[14:]
                left, value = rest.split(" as ", 1)
                parts = left.split()
                if len(parts) >= 2:
                    tokens.append(("SET_LLM_PARAM", parts[0], parts[1], value.strip()))
            elif line.startswith("fine tune ") and " on " in line and " input " in line and " output " in line:
                rest = line[10:]
                llm_var, right = rest.split(" on ", 1)
                df_part, right = right.split(" input ", 1)
                in_col, right = right.split(" output ", 1)
                out_col = right.strip()
                epochs = None
                lr = None
                if " epochs " in right:
                    out_col, epart = right.split(" epochs ", 1)
                    epochs = epart.strip().split()[0]
                if " lr " in right:
                    out_col, lpart = right.split(" lr ", 1)
                    lr = lpart.strip().split()[0]
                tokens.append(("FINE_TUNE_LLM", llm_var.strip(), df_part.strip(), in_col.strip(), out_col.strip(), epochs, lr))

            # ── Computer vision ────────────────────────────────────────────────
            elif line.startswith("load image ") and " as " in line:
                rest = line[11:]
                file_part, var = rest.split(" as ", 1)
                tokens.append(("LOAD_IMAGE", file_part.strip(), var.strip()))
            elif line.startswith("show image "):
                tokens.append(("SHOW_IMAGE", line[11:].strip()))
            elif line.startswith("save image ") and " as " in line:
                rest = line[11:]
                var, file_part = rest.split(" as ", 1)
                tokens.append(("SAVE_IMAGE", var.strip(), file_part.strip()))
            elif line.startswith("resize image ") and " to " in line and " as " in line:
                rest = line[13:]
                var, right = rest.split(" to ", 1)
                dims, res = right.split(" as ", 1)
                w_h = dims.split()
                if len(w_h) >= 2:
                    tokens.append(("RESIZE_IMAGE_CV", var.strip(), w_h[0], w_h[1], res.strip()))
            elif line.startswith("grayscale ") and " as " in line:
                rest = line[10:]
                var, res = rest.split(" as ", 1)
                tokens.append(("GRAYSCALE", var.strip(), res.strip()))
            elif line.startswith("detect objects in ") and " as " in line:
                rest = line[18:]
                var, res = rest.split(" as ", 1)
                model = None
                if " model " in res:
                    res, model = res.split(" model ", 1)
                tokens.append(("DETECT_OBJECTS", var.strip(), res.strip(), model.strip() if model else None))
            elif line.startswith("classify image ") and " using " in line and " as " in line:
                rest = line[15:]
                var, right = rest.split(" using ", 1)
                model, res = right.split(" as ", 1)
                tokens.append(("CLASSIFY_IMAGE", var.strip(), model.strip(), res.strip()))
            elif line.startswith("load video ") and " as " in line:
                rest = line[11:]
                src, var = rest.split(" as ", 1)
                tokens.append(("LOAD_VIDEO", src.strip(), var.strip()))
            elif line.startswith("capture frame from ") and " as " in line:
                rest = line[19:]
                vid, res = rest.split(" as ", 1)
                tokens.append(("CAPTURE_FRAME", vid.strip(), res.strip()))
            elif line.startswith("apply filter ") and " to " in line and " as " in line:
                rest = line[13:]
                filt, right = rest.split(" to ", 1)
                var, res = right.split(" as ", 1)
                strength = None
                if " strength " in res:
                    res, strength = res.split(" strength ", 1)
                tokens.append(("APPLY_FILTER", filt.strip(), var.strip(), res.strip(), strength.strip() if strength else None))
            elif line.startswith("augment image ") and " with " in line and " as " in line:
                rest = line[14:]
                var, right = rest.split(" with ", 1)
                ops, res = right.split(" as ", 1)
                tokens.append(("AUGMENT_IMAGE", var.strip(), _split_csv(ops), res.strip()))

            # ── Audio ─────────────────────────────────────────────────────────
            elif line.startswith("load audio ") and " as " in line:
                rest = line[11:]
                file_part, var = rest.split(" as ", 1)
                tokens.append(("LOAD_AUDIO", file_part.strip(), var.strip()))
            elif line.startswith("play audio "):
                tokens.append(("PLAY_AUDIO", line[11:].strip()))
            elif line.startswith("save audio ") and " as " in line:
                rest = line[11:]
                var, file_part = rest.split(" as ", 1)
                tokens.append(("SAVE_AUDIO", var.strip(), file_part.strip()))
            elif line.startswith("record audio ") and " as " in line:
                rest = line[13:]
                secs, var = rest.split(" as ", 1)
                tokens.append(("RECORD_AUDIO", secs.strip(), var.strip()))
            elif line.startswith("transcribe ") and " as " in line:
                rest = line[11:]
                var, res = rest.split(" as ", 1)
                model = None
                if " model " in res:
                    res, model = res.split(" model ", 1)
                tokens.append(("TRANSCRIBE_AUDIO", var.strip(), res.strip(), model.strip() if model else None))
            elif line.startswith("audio features of ") and " as " in line:
                rest = line[18:]
                var, res = rest.split(" as ", 1)
                tokens.append(("AUDIO_FEATURES", var.strip(), res.strip()))

            # ── Generative ────────────────────────────────────────────────────
            elif line.startswith("generate image ") and " as " in line:
                rest = line[15:]
                prompt, right = rest.split(" as ", 1)
                model = None
                width = None
                height = None
                steps = None
                if " model " in right:
                    right, model = right.split(" model ", 1)
                if " width " in right:
                    right, width = right.split(" width ", 1)
                if " height " in right:
                    right, height = right.split(" height ", 1)
                if " steps " in right:
                    right, steps = right.split(" steps ", 1)
                tokens.append(("GENERATE_IMAGE", prompt.strip(), right.strip(), model, width, height, steps))
            elif line.startswith("speak ") and " as " in line:
                rest = line[6:]
                text, right = rest.split(" as ", 1)
                voice = None
                if " voice " in right:
                    right, voice = right.split(" voice ", 1)
                tokens.append(("TEXT_TO_SPEECH", text.strip(), right.strip(), voice.strip() if voice else None))

            # ── NLP ───────────────────────────────────────────────────────────
            elif line.startswith("tokenize ") and " as " in line:
                rest = line[9:]
                var, res = rest.split(" as ", 1)
                tokens.append(("TOKENIZE_TEXT", var.strip(), res.strip()))
            elif line.startswith("sentiment of ") and " as " in line:
                rest = line[13:]
                var, res = rest.split(" as ", 1)
                tokens.append(("SENTIMENT", var.strip(), res.strip()))
            elif line.startswith("embed ") and " using " in line and " as " in line:
                rest = line[6:]
                var, right = rest.split(" using ", 1)
                model, res = right.split(" as ", 1)
                tokens.append(("EMBED_TEXT", var.strip(), model.strip(), res.strip()))
            elif line.startswith("summarize ") and " as " in line:
                rest = line[10:]
                var, res = rest.split(" as ", 1)
                max_words = None
                if " max words " in res:
                    res, max_words = res.split(" max words ", 1)
                tokens.append(("SUMMARIZE_TEXT", var.strip(), res.strip(), max_words.strip() if max_words else None))
            elif line.startswith("translate ") and " to " in line and " as " in line:
                rest = line[10:]
                var, right = rest.split(" to ", 1)
                lang, res = right.split(" as ", 1)
                tokens.append(("TRANSLATE_TEXT", var.strip(), lang.strip(), res.strip()))

            # ── AI / ML ───────────────────────────────────────────────────────
            elif line.startswith("teach ai with ") or line.startswith("teach chatbot with "):
                target = "ai" if line.startswith("teach ai") else "chatbot"
                data = line.split(" with ")[1].strip()
                tokens.append(("TEACH", target, data))
            elif line.startswith("ask ai prediction for "):
                tokens.append(("ASK_PREDICT", line[22:].strip()))
            elif line.startswith("predict using ai"):
                tokens.append(("ASK_PREDICT", "1"))
            elif line.startswith("predict using"):
                kwargs = {}
                j = i + 1
                while j < len(lines):
                    curr = lines[j]
                    if not curr.strip(): j += 1; continue
                    if curr[0] in " \t\xa0":
                        if "=" in curr:
                            k, v = curr.split("=", 1)
                            kwargs[k.strip()] = v.strip()
                        j += 1
                    else:
                        break
                tokens.append(("PREDICT", kwargs))
                i = j - 1
            elif line == "create smart brain":
                tokens.append(("CREATE_BRAIN", "smart"))
            elif line == "create language brain":
                tokens.append(("CREATE_BRAIN", "language"))
            elif line.startswith("learn from "):
                tokens.append(("TEACH", "brain", line[11:].strip()))

            # ── Package management ────────────────────────────────────────────
            elif line.startswith("get package "):
                tokens.append(("INSTALL", line[12:].strip()))
            elif line.startswith("share package "):
                tokens.append(("MEDIA", "share", line[14:].strip()))
            elif line.startswith("install "):
                tokens.append(("INSTALL", line[8:].strip()))
            elif line.startswith("search package "):
                tokens.append(("SEARCH_PKG", line[15:].strip()))

            # ── OS info ───────────────────────────────────────────────────────
            elif line.startswith("show battery") or line.startswith("show memory") or line.startswith("show cpu"):
                tokens.append(("OS", line[5:].strip()))

            # ── Auth / bot ────────────────────────────────────────────────────
            elif line == "create chatbot":
                tokens.append(("CREATE_BOT", "chatbot"))
            elif line == "create assistant":
                tokens.append(("CREATE_BOT", "assistant"))

            # ── DB save / write (file) ────────────────────────────────────────
            elif line.startswith("save ") and " in " in line:
                parts = line[5:].split(" in ")
                tokens.append(("WRITE", parts[1].strip(), parts[0].strip()))
            elif line.startswith("save database ") and " as " in line:
                parts = line[14:].split(" as ", 1)
                tokens.append(("SAVE_DB", parts[0].strip(), parts[1].strip()))

            # ── Ask AI ────────────────────────────────────────────────────────
            elif line.startswith("ask ai "):
                rest = line[7:].strip()
                if " as " in rest:
                    prompt_part, var = rest.rsplit(" as ", 1)
                    tokens.append(("ASK_AI", prompt_part.strip(), var.strip()))
                else:
                    tokens.append(("ASK_AI", rest, "ai_response"))
            elif line.startswith("ask assistant "):
                rest = line[14:].strip()
                if " as " in rest:
                    prompt_part, var = rest.rsplit(" as ", 1)
                    tokens.append(("ASK_AI", prompt_part.strip(), var.strip()))
                else:
                    tokens.append(("ASK_AI", rest, "ai_response"))
            elif line.startswith("ask language brain "):
                rest = line[19:].strip()
                if " as " in rest:
                    prompt_part, var = rest.rsplit(" as ", 1)
                    tokens.append(("ASK_AI", prompt_part.strip(), var.strip()))
                else:
                    tokens.append(("ASK_AI", rest, "ai_response"))

            # ── Class definition ──────────────────────────────────────────────
            elif line.startswith("create class "):
                name = line[13:].strip()
                body = []
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                    if lines[j].strip(): body.append(lines[j].rstrip())
                    j += 1
                tokens.append(("CLASS", name, body))
                i = j - 1

            elif line.startswith("create object ") and " as " in line:
                parts = line[14:].split(" as ")
                tokens.append(("CREATE_OBJ", parts[0].strip(), parts[1].strip()))

            elif line.startswith("create ") and " as " in line:
                parts = line[7:].split(" as ")
                tokens.append(("CREATE_OBJ", parts[0].strip(), parts[1].strip()))

            # ── Try / otherwise ───────────────────────────────────────────────
            elif line == "try":
                try_body, catch_body = [], []
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                    if lines[j].strip(): try_body.append(lines[j].rstrip())
                    j += 1
                if j < len(lines) and lines[j].strip() == "otherwise":
                    j += 1
                    while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                        if lines[j].strip(): catch_body.append(lines[j].rstrip())
                        j += 1
                tokens.append(("TRY", try_body, catch_body))
                i = j - 1

            # ── Draw (ASCII) ──────────────────────────────────────────────────
            elif line.startswith("draw "):
                parts = line[5:].split()
                if len(parts) >= 2: tokens.append(("DRAW", parts[0], parts[1]))



            # ── Convert ───────────────────────────────────────────────────────
            elif line.startswith("convert ") and " to " in line:
                parts = line[8:].split(" to ")
                tokens.append(("CONVERT", parts[0].strip(), parts[1].strip()))

            # ── Set (dict / list / plain) ─────────────────────────────────────
            elif line.startswith("set ") and " as" in line:
                parts = line[4:].split(" as", 1)
                var_name = parts[0].strip()
                right_side = parts[1].strip()

                import re as _re_lex
                _idx_match = _re_lex.fullmatch(r'(\w+)\[(-?\d+|\w+)\]', var_name)
                if _idx_match and right_side:
                    tokens.append(("SET_INDEX", _idx_match.group(1), _idx_match.group(2), right_side))
                else:
                    if not right_side:
                        j = i + 1
                        while j < len(lines) and not lines[j].strip(): j += 1
                        if j < len(lines) and lines[j].strip() in ["{", "["]:
                            right_side = lines[j].strip()
                            i = j

                    if right_side == "{":
                        dict_items = {}
                        j = i + 1
                        while j < len(lines):
                            curr = lines[j].strip()
                            if curr == "}": break
                            if ":" in curr:
                                k, v = curr.split(":", 1)
                                dict_items[k.strip()] = v.strip()
                            j += 1
                        tokens.append(("SET_DICT", var_name, dict_items))
                        i = j
                    elif right_side == "[":
                        list_items = []
                        j = i + 1
                        while j < len(lines):
                            curr = lines[j].strip()
                            if curr == "]": break
                            if curr: list_items.append(curr.replace('"', '').strip())
                            j += 1
                        tokens.append(("SET", var_name, "[" + ",".join(list_items) + "]"))
                        i = j
                    else:
                        tokens.append(("SET", var_name, right_side))

            # ── Calculate ─────────────────────────────────────────────────────
            elif line.startswith("calculate "):
                parts = line[10:].split(" as", 1)
                result_name = parts[0].strip()
                expression = parts[1].strip() if len(parts) > 1 else ""
                if not expression:
                    j = i + 1
                    while j < len(lines):
                        curr = lines[j]
                        if not curr.strip(): j += 1; continue
                        if curr[0] in " \t\xa0":
                            expression += " " + curr.strip();
                            j += 1
                        else:
                            break
                    i = j - 1
                tokens.append(("CALCULATE", result_name, expression.strip()))

            # ── Ask (user input) ──────────────────────────────────────────────
            elif line.startswith("ask "):
                rest = line[4:].strip()
                if rest.startswith('"'):
                    end_quote = rest.index('"', 1)
                    prompt_text = rest[1:end_quote].rstrip()
                    if not prompt_text.endswith(" "): prompt_text += " "
                    after = rest[end_quote + 1:].strip().lstrip(",").strip()
                    tokens.append(("ASK", after if after else rest, prompt_text if after else ""))
                else:
                    tokens.append(("ASK", rest, ""))

            # ── Read / write file ──────────────────────────────────────────────
            elif line.startswith("read "):
                rest = line[5:].strip()
                if " as " in rest:
                    parts = rest.split(" as ", 1)
                    tokens.append(("READ", parts[0].strip(), parts[1].strip()))
                else:
                    tokens.append(("READ", rest, "content"))

            elif line.startswith("write "):
                parts = line[6:].split(" as ")
                if len(parts) == 2: tokens.append(("WRITE", parts[0].strip(), parts[1].strip()))

            # ── Function definition ───────────────────────────────────────────
            elif line.startswith("define "):
                parts = line.split()
                function_name, parameters = parts[1], parts[2:]
                body = []
                j = i + 1
                while j < len(lines):
                    if not lines[j].strip(): j += 1; continue
                    if lines[j][0] in " \t\xa0":
                        body.append(lines[j].rstrip()); j += 1
                    else:
                        break
                tokens.append(("FUNCTION", function_name, parameters, body))
                i = j - 1

            elif line.startswith("return "):
                tokens.append(("RETURN", line[7:].strip()))

            # ── Call ──────────────────────────────────────────────────────────
            elif line.startswith("call "):
                content = line[5:].strip()
                pieces, current, inside_quotes = [], "", False
                for char in content:
                    if char == '"':
                        current += char; inside_quotes = not inside_quotes
                    elif char == " " and not inside_quotes:
                        if current: pieces.append(current); current = ""
                    else:
                        current += char
                if current: pieces.append(current)
                tokens.append(("CALL", pieces[0], pieces[1:]))

            # ── Break ─────────────────────────────────────────────────────────
            elif line == "break":
                tokens.append(("BREAK",))

            # ── Show ──────────────────────────────────────────────────────────
            elif line.startswith("show "):
                tokens.append(("SHOW", line[5:].strip()))

            # ── ADD TABLE ─────────────────────────────────────────────────────
            elif line.startswith("add ") and '"' in line:
                parts = line.split(" ", 2)
                tokens.append(("ADD_TABLE", parts[1].strip(), parts[2].strip()))

            # ── If / else if / otherwise ──────────────────────────────────────
            elif line.startswith("if "):
                condition = line[3:].strip()
                true_body, false_body = [], []

                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                    if lines[j].strip(): true_body.append(lines[j].rstrip())
                    j += 1

                while j < len(lines):
                    stripped = lines[j].strip()
                    if stripped in ("otherwise", "else"):
                        j += 1
                        while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                            if lines[j].strip(): false_body.append(lines[j].rstrip())
                            j += 1
                        break
                    elif stripped.startswith("else if ") or stripped.startswith("elif "):
                        nested_cond = stripped[8:].strip() if stripped.startswith("else if ") else stripped[5:].strip()
                        nested_true, nested_false = [], []
                        j += 1
                        while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                            if lines[j].strip(): nested_true.append(lines[j].rstrip())
                            j += 1
                        while j < len(lines):
                            s2 = lines[j].strip()
                            if s2 in ("otherwise", "else"):
                                j += 1
                                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                                    if lines[j].strip(): nested_false.append(lines[j].rstrip())
                                    j += 1
                                break
                            elif s2.startswith("else if ") or s2.startswith("elif "):
                                break
                            else:
                                break
                        false_body = [f"__IF__{nested_cond}__THEN__{nested_true}__ELSE__{nested_false}"]
                        break
                    else:
                        break

                tokens.append(("IF", condition, true_body, false_body))
                i = j - 1

            # ── While ─────────────────────────────────────────────────────────
            elif line.startswith("while "):
                condition = line[6:].strip()
                body = []
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                    if lines[j].strip(): body.append(lines[j].rstrip())
                    j += 1
                tokens.append(("WHILE", condition, body))
                i = j - 1

            # ── For ───────────────────────────────────────────────────────────
            elif line.startswith("for "):
                parts = line[4:].strip().split(" in ")
                variable = parts[0].strip()
                iterable = parts[1].strip()
                body = []
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                    if lines[j].strip(): body.append(lines[j].rstrip())
                    j += 1
                tokens.append(("FOR", variable, iterable, body))
                i = j - 1

            # ── Repeat ────────────────────────────────────────────────────────
            elif line.startswith("repeat "):
                count = line[7:].strip()
                if count.endswith(" times"):
                    count = count[:-6].strip()

                body = []
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t\xa0"):
                    if lines[j].strip(): body.append(lines[j].rstrip())
                    j += 1
                tokens.append(("REPEAT", count, body))
                i = j - 1

            i += 1
        return tokens