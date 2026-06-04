# =============================================================================
#  Homo Language — Parser
#  Converts the flat token list produced by Lexer into an AST (list of nodes).
#  Each token is a tuple whose first element is a TYPE string.
# =============================================================================

from ast_nodes import *


class Parser:
    def parse(self, tokens):
        ast = []
        for token in tokens:
            t = token[0]

            # ── Core I/O ──────────────────────────────────────────────────────
            if   t == "SHOW":       ast.append(ShowNode(token[1]))
            elif t == "ASK":        ast.append(AskNode(token[1], token[2]))
            elif t == "LOG":        ast.append(LogNode(token[1]))

            # ── Variables ─────────────────────────────────────────────────────
            elif t == "SET":        ast.append(SetNode(token[1], token[2]))
            elif t == "SET_DICT":   ast.append(SetDictNode(token[1], token[2]))
            elif t == "SET_INDEX":  ast.append(SetIndexNode(token[1], token[2], token[3]))
            elif t == "CALCULATE":  ast.append(CalculateNode(token[1], token[2]))

            # ── Control flow ──────────────────────────────────────────────────
            elif t == "IF":         ast.append(IfNode(token[1], token[2], token[3]))
            elif t == "WHILE":      ast.append(WhileNode(token[1], token[2]))
            elif t == "FOR":        ast.append(ForNode(token[1], token[2], token[3]))
            elif t == "REPEAT":     ast.append(RepeatNode(token[1], token[2]))
            elif t == "BREAK":      ast.append(BreakNode())
            elif t == "TRY":        ast.append(TryNode(token[1], token[2]))
            elif t == "ASSERT":     ast.append(AssertNode(token[1], token[2]))

            # ── Functions / modules ───────────────────────────────────────────
            elif t == "FUNCTION":   ast.append(FunctionNode(token[1], token[2], token[3]))
            elif t == "RETURN":     ast.append(ReturnNode(token[1]))
            elif t == "CALL":       ast.append(CallNode(token[1], token[2]))
            elif t == "USE":        ast.append(UseNode(token[1]))
            elif t == "EXPORT":     ast.append(ExportNode(token[1]))
            elif t == "INSTALL":    ast.append(InstallNode(token[1]))

            # ── OOP ───────────────────────────────────────────────────────────
            elif t == "CLASS":          ast.append(ClassNode(token[1], token[2]))
            elif t == "CREATE_OBJ":     ast.append(CreateObjNode(token[1], token[2]))
            elif t == "INHERIT_CLASS":  ast.append(InheritClassNode(token[1], token[2]))

            # ── File system ───────────────────────────────────────────────────
            elif t == "READ":        ast.append(ReadNode(token[1], token[2]))
            elif t == "WRITE":       ast.append(WriteNode(token[2], token[1]))
            elif t == "DELETE_FILE": ast.append(DeleteFileNode(token[1]))
            elif t == "MAKE_DIR":    ast.append(MakeDirNode(token[1]))
            elif t == "LIST_FILES":  ast.append(ListFilesNode(token[1], token[2]))
            elif t == "COPY":        ast.append(CopyNode(token[1], token[2]))

            # ── List / collection helpers ──────────────────────────────────────
            elif t == "APPEND":     ast.append(AppendNode(token[1], token[2]))
            elif t == "REMOVE":     ast.append(RemoveNode(token[1], token[2]))
            elif t == "COUNT":      ast.append(CountNode(token[1], token[2], token[3]))
            elif t == "SORT":       ast.append(SortNode(token[1], token[2]))
            elif t == "REVERSE":    ast.append(ReverseNode(token[1], token[2]))
            elif t == "FILTER":     ast.append(FilterNode(token[1], token[2], token[3]))
            elif t == "MAP":        ast.append(MapNode(token[1], token[2], token[3]))
            elif t == "JOIN":       ast.append(JoinNode(token[1], token[2], token[3]))
            elif t == "SPLIT":      ast.append(SplitNode(token[1], token[2], token[3]))

            # ── Math / type helpers ────────────────────────────────────────────
            elif t == "CONVERT":    ast.append(ConvertNode(token[1], token[2]))
            elif t == "CHECK":      ast.append(CheckNode(token[1], token[2]))

            # ── System / environment ───────────────────────────────────────────
            elif t == "SET_ENV":    ast.append(SetEnvNode(token[1], token[2]))
            elif t == "GET_ENV":    ast.append(GetEnvNode(token[1], token[2]))
            elif t == "SLEEP":      ast.append(SleepNode(token[1]))
            elif t == "RUN":        ast.append(RunNode(token[1]))
            elif t == "OS":         ast.append(OSNode(token[1]))
            elif t == "TASK":       ast.append(TaskNode(token[1]))

            # ── Networking ────────────────────────────────────────────────────
            elif t == "VISIT":          ast.append(VisitNode(token[1]))
            elif t == "FETCH":          ast.append(FetchNode(token[1], token[2]))
            elif t == "POST":           ast.append(PostNode(token[1], token[2], token[3]))
            elif t == "CONNECT_SOCKET": ast.append(ConnectSocketNode(token[1]))
            elif t == "SEND_SOCKET":    ast.append(SendSocketNode(token[1]))
            elif t == "SERVE":          ast.append(ServeNode(token[1]))

            # ── Database ──────────────────────────────────────────────────────
            elif t == "OPEN_DB":      ast.append(OpenDBNode(token[1]))
            elif t == "SAVE_DB":      ast.append(SaveDBNode(token[1], token[2]))
            elif t == "CONNECT_DB":   ast.append(ConnectDBNode(token[1], token[2]))
            elif t == "QUERY_DB":     ast.append(QueryDBNode(token[1], token[2], token[3]))
            elif t == "DELETE_DB":    ast.append(DeleteDBNode(token[1]))
            elif t == "CREATE_TABLE": ast.append(CreateTableNode(token[1]))
            elif t == "ADD_TABLE":    ast.append(AddToTableNode(token[1], token[2]))
            elif t == "PRINT_TABLE":  ast.append(PrintTableNode(token[1]))

            # ── Crypto / security ─────────────────────────────────────────────
            elif t == "HASH":       ast.append(HashNode(token[1], token[2]))
            elif t == "ENCRYPT":    ast.append(EncryptNode(token[1], token[2], token[3] if len(token) > 3 else "result"))
            elif t == "DECRYPT":    ast.append(DecryptNode(token[1], token[2], token[3] if len(token) > 3 else "result"))
            elif t == "LOGIN":      ast.append(LoginNode(token[1]))
            elif t == "LOGOUT":     ast.append(LogoutNode())
            elif t == "SEND_EMAIL": ast.append(SendEmailNode(token[1], token[2], token[3]))

            # ── PDF / Image export ────────────────────────────────────────────
            elif t == "EXPORT_PDF":   ast.append(ExportPDFNode(token[1]))
            elif t == "RESIZE_IMAGE": ast.append(ResizeImageNode(token[1], token[2], token[3]))

            # ── Visualization / utility ────────────────────────────────────────
            elif t == "SHOW_CHART":     ast.append(ShowChartNode(token[1], token[2]))
            elif t == "DRAW":           ast.append(DrawNode(token[1], token[2]))
            elif t == "MEDIA":          ast.append(MediaNode(token[1], token[2]))

            # ── Data Science — Pandas / NumPy ─────────────────────────────────
            # token formats emitted by lexer:
            #   ("LOAD_DATA",      source, variable, options_dict)
            #   ("SAVE_DATA",      variable, file, options_dict)
            #   ("SHOW_DATA",      variable, rows)
            #   ("DESCRIBE_DATA",  variable)
            #   ("SELECT_COLS",    columns_list, dataframe, result)
            #   ("DROP_COLS",      columns_list, dataframe)
            #   ("RENAME_COL",     old, new, dataframe)
            #   ("FILTER_ROWS",    dataframe, condition, result)
            #   ("GROUP_BY",       dataframe, by_col, agg_func, agg_col, result)
            #   ("MERGE_DATA",     df1, df2, on, how, result)
            #   ("FILL_MISSING",   dataframe, value, column_or_None)
            #   ("DROP_MISSING",   dataframe)
            #   ("ADD_COLUMN",     column, dataframe, expression)
            #   ("NORMALIZE",      dataframe, column_or_None)
            #   ("STANDARDIZE",    dataframe, column_or_None)
            #   ("ENCODE",         dataframe, column)
            #   ("SPLIT_DATA",     dataframe, train_var, test_var, ratio, target_or_None)
            #   ("PLOT",           variable, chart_type, title, x_col, y_col, save_as)
            #   ("STATS",          variable, result)
            elif t == "LOAD_DATA":     ast.append(LoadDataNode(token[1], token[2], token[3] if len(token) > 3 else {}))
            elif t == "SAVE_DATA":     ast.append(SaveDataNode(token[1], token[2], token[3] if len(token) > 3 else {}))
            elif t == "SHOW_DATA":     ast.append(ShowDataNode(token[1], token[2] if len(token) > 2 else 10))
            elif t == "DESCRIBE_DATA": ast.append(DescribeDataNode(token[1]))
            elif t == "SELECT_COLS":   ast.append(SelectColumnsNode(token[1], token[2], token[3]))
            elif t == "DROP_COLS":     ast.append(DropColumnsNode(token[1], token[2]))
            elif t == "RENAME_COL":    ast.append(RenameColumnNode(token[1], token[2], token[3]))
            elif t == "FILTER_ROWS":   ast.append(FilterRowsNode(token[1], token[2], token[3]))
            elif t == "GROUP_BY":      ast.append(GroupByNode(token[1], token[2], token[3], token[4], token[5]))
            elif t == "MERGE_DATA":    ast.append(MergeDataNode(token[1], token[2], token[3], token[4], token[5]))
            elif t == "FILL_MISSING":  ast.append(FillMissingNode(token[1], token[2], token[3] if len(token) > 3 else None))
            elif t == "DROP_MISSING":  ast.append(DropMissingNode(token[1]))
            elif t == "ADD_COLUMN":    ast.append(AddColumnNode(token[1], token[2], token[3]))
            elif t == "NORMALIZE":     ast.append(NormalizeNode(token[1], token[2] if len(token) > 2 else None))
            elif t == "STANDARDIZE":   ast.append(StandardizeNode(token[1], token[2] if len(token) > 2 else None))
            elif t == "ENCODE":        ast.append(EncodeNode(token[1], token[2]))
            elif t == "SPLIT_DATA":    ast.append(SplitDataNode(token[1], token[2], token[3],
                                                                 token[4] if len(token) > 4 else 0.8,
                                                                 token[5] if len(token) > 5 else None))
            elif t == "PLOT":          ast.append(PlotNode(token[1], token[2], token[3],
                                                           token[4] if len(token) > 4 else None,
                                                           token[5] if len(token) > 5 else None,
                                                           token[6] if len(token) > 6 else None))
            elif t == "STATS":         ast.append(StatsNode(token[1], token[2]))

            # ── Machine Learning — scikit-learn ───────────────────────────────
            # token formats:
            #   ("CREATE_MODEL",      model_type, name, params_dict)
            #   ("SET_PARAM",         model, param, value)
            #   ("TRAIN_MODEL",       model, dataframe, target, features_list_or_None)
            #   ("EVALUATE_MODEL",    model, dataframe, result, target, metric)
            #   ("PREDICT",           model, source, result)
            #   ("SAVE_MODEL",        name, file)
            #   ("LOAD_MODEL",        file, name)
            #   ("TUNE_MODEL",        model, dataframe, target, trials, result)
            #   ("CROSS_VALIDATE",    model, dataframe, target, folds, result)
            #   ("FEATURE_IMPORTANCE",model, result)
            #   ("CONFUSION_MATRIX",  model, dataframe, result, target)
            elif t == "CREATE_MODEL":       ast.append(CreateModelNode(token[1], token[2], token[3] if len(token) > 3 else {}))
            elif t == "SET_PARAM":          ast.append(SetParamNode(token[1], token[2], token[3]))
            elif t == "TRAIN_MODEL":        ast.append(TrainModelNode(token[1], token[2], token[3], token[4] if len(token) > 4 else None))
            elif t == "EVALUATE_MODEL":     ast.append(EvaluateModelNode(token[1], token[2], token[3],
                                                                          token[4] if len(token) > 4 else None,
                                                                          token[5] if len(token) > 5 else None))
            elif t == "PREDICT":            ast.append(PredictNode(token[1], token[2], token[3]))
            elif t == "SAVE_MODEL":         ast.append(SaveModelNode(token[1], token[2]))
            elif t == "LOAD_MODEL":         ast.append(LoadModelNode(token[1], token[2]))
            elif t == "TUNE_MODEL":         ast.append(TuneModelNode(token[1], token[2], token[3], token[4], token[5]))
            elif t == "CROSS_VALIDATE":     ast.append(CrossValidateNode(token[1], token[2], token[3], token[4], token[5]))
            elif t == "FEATURE_IMPORTANCE": ast.append(FeatureImportanceNode(token[1], token[2]))
            elif t == "CONFUSION_MATRIX":   ast.append(ConfusionMatrixNode(token[1], token[2], token[3],
                                                                            token[4] if len(token) > 4 else None))

            # ── Deep Learning — PyTorch ────────────────────────────────────────
            # token formats:
            #   ("CREATE_NETWORK",   name, layers_list, activation, output_activation)
            #   ("TRAIN_NETWORK",    name, df, target, epochs, batch, lr, loss, optimizer, features)
            #   ("PREDICT_NETWORK",  name, source, result)
            #   ("SAVE_NETWORK",     name, file)
            #   ("LOAD_NETWORK",     file, name)
            #   ("SET_LOSS",         network, loss)
            #   ("SET_OPTIMIZER",    network, optimizer, lr)
            elif t == "CREATE_NETWORK":  ast.append(CreateNetworkNode(token[1], token[2],
                                                                       token[3] if len(token) > 3 else "relu",
                                                                       token[4] if len(token) > 4 else None))
            elif t == "TRAIN_NETWORK":   ast.append(TrainNetworkNode(
                                                      token[1], token[2], token[3],
                                                      token[4] if len(token) > 4 else 10,
                                                      token[5] if len(token) > 5 else 32,
                                                      token[6] if len(token) > 6 else 0.001,
                                                      token[7] if len(token) > 7 else "mse",
                                                      token[8] if len(token) > 8 else "adam",
                                                      token[9] if len(token) > 9 else None))
            elif t == "PREDICT_NETWORK": ast.append(PredictNetworkNode(token[1], token[2], token[3]))
            elif t == "SAVE_NETWORK":    ast.append(SaveNetworkNode(token[1], token[2]))
            elif t == "LOAD_NETWORK":    ast.append(LoadNetworkNode(token[1], token[2]))
            elif t == "SET_LOSS":        ast.append(SetLossNode(token[1], token[2]))
            elif t == "SET_OPTIMIZER":   ast.append(SetOptimizerNode(token[1], token[2],
                                                                      token[3] if len(token) > 3 else 0.001))

            # ── Local LLM ─────────────────────────────────────────────────────
            # token formats:
            #   ("LOAD_LLM",       source, variable, options_dict)
            #   ("PROMPT_LLM",     llm_var, prompt, result, options_dict)
            #   ("SET_LLM_PARAM",  llm_var, param, value)
            #   ("FINE_TUNE_LLM",  llm_var, df, input_col, output_col, epochs, lr)
            elif t == "LOAD_LLM":      ast.append(LoadLLMNode(token[1], token[2], token[3] if len(token) > 3 else {}))
            elif t == "PROMPT_LLM":    ast.append(PromptLLMNode(token[1], token[2], token[3], token[4] if len(token) > 4 else {}))
            elif t == "SET_LLM_PARAM": ast.append(SetLLMParamNode(token[1], token[2], token[3]))
            elif t == "FINE_TUNE_LLM": ast.append(FineTuneLLMNode(token[1], token[2], token[3], token[4],
                                                                    token[5] if len(token) > 5 else 3,
                                                                    token[6] if len(token) > 6 else 2e-5))

            # ── Computer Vision ────────────────────────────────────────────────
            # token formats:
            #   ("LOAD_IMAGE",      file, variable)
            #   ("SHOW_IMAGE",      variable)
            #   ("SAVE_IMAGE",      variable, file)
            #   ("RESIZE_IMAGE_CV", variable, width, height, result)
            #   ("GRAYSCALE",       variable, result)
            #   ("DETECT_OBJECTS",  variable, result, model_or_None)
            #   ("CLASSIFY_IMAGE",  variable, model, result)
            #   ("LOAD_VIDEO",      source, variable)
            #   ("CAPTURE_FRAME",   video_var, result)
            #   ("APPLY_FILTER",    filter_name, variable, result, strength)
            #   ("AUGMENT_IMAGE",   variable, ops_list, result)
            elif t == "LOAD_IMAGE":      ast.append(LoadImageNode(token[1], token[2]))
            elif t == "SHOW_IMAGE":      ast.append(ShowImageNode(token[1]))
            elif t == "SAVE_IMAGE":      ast.append(SaveImageNode(token[1], token[2]))
            elif t == "RESIZE_IMAGE_CV": ast.append(ResizeImageCVNode(token[1], token[2], token[3], token[4]))
            elif t == "GRAYSCALE":       ast.append(GrayscaleNode(token[1], token[2]))
            elif t == "DETECT_OBJECTS":  ast.append(DetectObjectsNode(token[1], token[2], token[3] if len(token) > 3 else None))
            elif t == "CLASSIFY_IMAGE":  ast.append(ClassifyImageNode(token[1], token[2], token[3]))
            elif t == "LOAD_VIDEO":      ast.append(LoadVideoNode(token[1], token[2]))
            elif t == "CAPTURE_FRAME":   ast.append(CaptureFrameNode(token[1], token[2]))
            elif t == "APPLY_FILTER":    ast.append(ApplyFilterNode(token[1], token[2], token[3],
                                                                     token[4] if len(token) > 4 else 1.0))
            elif t == "AUGMENT_IMAGE":   ast.append(AugmentImageNode(token[1], token[2], token[3]))

            # ── Audio ─────────────────────────────────────────────────────────
            # token formats:
            #   ("LOAD_AUDIO",       file, variable)
            #   ("PLAY_AUDIO",       variable)
            #   ("SAVE_AUDIO",       variable, file)
            #   ("RECORD_AUDIO",     seconds, variable)
            #   ("TRANSCRIBE_AUDIO", audio_var, result, model)
            #   ("AUDIO_FEATURES",   variable, result)
            elif t == "LOAD_AUDIO":       ast.append(LoadAudioNode(token[1], token[2]))
            elif t == "PLAY_AUDIO":       ast.append(PlayAudioNode(token[1]))
            elif t == "SAVE_AUDIO":       ast.append(SaveAudioNode(token[1], token[2]))
            elif t == "RECORD_AUDIO":     ast.append(RecordAudioNode(token[1], token[2]))
            elif t == "TRANSCRIBE_AUDIO": ast.append(TranscribeAudioNode(token[1], token[2],
                                                                           token[3] if len(token) > 3 else "base"))
            elif t == "AUDIO_FEATURES":   ast.append(AudioFeaturesNode(token[1], token[2]))

            # ── Generative — local ────────────────────────────────────────────
            # token formats:
            #   ("GENERATE_IMAGE",  prompt, variable, model, width, height, steps)
            #   ("TEXT_TO_SPEECH",  text, file_or_None, voice_or_None)
            elif t == "GENERATE_IMAGE": ast.append(GenerateImageNode(
                                            token[1], token[2],
                                            token[3] if len(token) > 3 else "stabilityai/stable-diffusion-2-1",
                                            token[4] if len(token) > 4 else 512,
                                            token[5] if len(token) > 5 else 512,
                                            token[6] if len(token) > 6 else 30))
            elif t == "TEXT_TO_SPEECH": ast.append(TextToSpeechNode(token[1],
                                                                      token[2] if len(token) > 2 else None,
                                                                      token[3] if len(token) > 3 else None))

            # ── NLP helpers ───────────────────────────────────────────────────
            # token formats:
            #   ("TOKENIZE_TEXT",   variable, result)
            #   ("SENTIMENT",       variable, result)
            #   ("EMBED_TEXT",      variable, model, result)
            #   ("SUMMARIZE_TEXT",  variable, result, max_words)
            #   ("TRANSLATE_TEXT",  variable, language, result)
            elif t == "TOKENIZE_TEXT":  ast.append(TokenizeTextNode(token[1], token[2]))
            elif t == "SENTIMENT":      ast.append(SentimentNode(token[1], token[2]))
            elif t == "EMBED_TEXT":     ast.append(EmbedTextNode(token[1], token[2], token[3]))
            elif t == "SUMMARIZE_TEXT": ast.append(SummarizeTextNode(token[1], token[2],
                                                                       token[3] if len(token) > 3 else 100))
            elif t == "TRANSLATE_TEXT": ast.append(TranslateTextNode(token[1], token[2], token[3]))

            # ── Unknown token: warn but continue ─────────────────────────────
            else:
                print(f"[homo parser] Warning: unknown token type '{t}' — skipped")

        return ast
