# =============================================================================
#  Homo Language — AST Nodes
#  Every node represents one statement in a .homo source file.
#  Naming convention:  <Keyword>Node
# =============================================================================


# ── Core I/O ─────────────────────────────────────────────────────────────────

class ShowNode:
    """show <value>   →  print to stdout"""
    def __init__(self, value): self.value = value
    def __repr__(self): return f"ShowNode({self.value})"

class AskNode:
    """ask "prompt", <variable>   →  read user input"""
    def __init__(self, variable, prompt=""):
        self.variable = variable
        self.prompt   = prompt
    def __repr__(self): return f"AskNode({self.variable}, {self.prompt!r})"

class LogNode:
    """log <message>   →  write to log file"""
    def __init__(self, message): self.message = message
    def __repr__(self): return f"LogNode({self.message})"


# ── Variables ─────────────────────────────────────────────────────────────────

class SetNode:
    """set <name> as <value>"""
    def __init__(self, name, value): self.name, self.value = name, value
    def __repr__(self): return f"SetNode({self.name}, {self.value})"

class SetDictNode:
    """set <name> as { key: value ... }"""
    def __init__(self, name, pairs): self.name, self.pairs = name, pairs
    def __repr__(self): return f"SetDictNode({self.name}, {self.pairs})"

class SetIndexNode:
    """set <list>[<index>] as <value>"""
    def __init__(self, name, index, value):
        self.name, self.index, self.value = name, index, value
    def __repr__(self): return f"SetIndexNode({self.name}[{self.index}], {self.value})"

class CalculateNode:
    """calculate <result> as <expression>"""
    def __init__(self, result, expression):
        self.result     = result
        self.expression = expression
    def __repr__(self): return f"CalculateNode({self.result}, {self.expression})"


# ── Control flow ──────────────────────────────────────────────────────────────

class IfNode:
    """if <condition> / otherwise"""
    def __init__(self, condition, true_body, false_body):
        self.condition  = condition
        self.true_body  = true_body
        self.false_body = false_body
    def __repr__(self): return f"IfNode({self.condition})"

class WhileNode:
    """while <condition>  (indented body)"""
    def __init__(self, condition, body):
        self.condition, self.body = condition, body
    def __repr__(self): return f"WhileNode({self.condition})"

class ForNode:
    """for <variable> in <iterable>  (indented body)"""
    def __init__(self, variable, iterable, body):
        self.variable, self.iterable, self.body = variable, iterable, body
    def __repr__(self): return f"ForNode({self.variable}, {self.iterable})"

class RepeatNode:
    """repeat <count> times  (indented body)"""
    def __init__(self, count, body):
        self.count, self.body = count, body
    def __repr__(self): return f"RepeatNode({self.count})"

class BreakNode:
    """break  →  exit current loop"""
    def __repr__(self): return "BreakNode()"

class TryNode:
    """try  /  otherwise  (indented bodies)"""
    def __init__(self, try_body, catch_body):
        self.try_body, self.catch_body = try_body, catch_body
    def __repr__(self): return "TryNode()"

class AssertNode:
    """assert <condition> otherwise <message>"""
    def __init__(self, condition, message):
        self.condition, self.message = condition, message
    def __repr__(self): return f"AssertNode({self.condition})"


# ── Functions / modules ───────────────────────────────────────────────────────

class FunctionNode:
    """define <name> <param1> <param2> ...  (indented body)"""
    def __init__(self, name, parameters, body):
        self.name, self.parameters, self.body = name, parameters, body
    def __repr__(self): return f"FunctionNode({self.name}, {self.parameters})"

class ReturnNode:
    """return <expression>"""
    def __init__(self, expression): self.expression = expression
    def __repr__(self): return f"ReturnNode({self.expression})"

class CallNode:
    """call <name> <arg1> <arg2> ..."""
    def __init__(self, name, arguments):
        self.name, self.arguments = name, arguments
    def __repr__(self): return f"CallNode({self.name}, {self.arguments})"

class UseNode:
    """use <module>   →  import a .homo file or Python module"""
    def __init__(self, module_name): self.module_name = module_name
    def __repr__(self): return f"UseNode({self.module_name})"

class ExportNode:
    """export <name>   →  make a symbol visible to importers"""
    def __init__(self, name): self.name = name
    def __repr__(self): return f"ExportNode({self.name})"

class InstallNode:
    """install <package>   →  pip install at runtime"""
    def __init__(self, package): self.package = package
    def __repr__(self): return f"InstallNode({self.package})"


# ── OOP ───────────────────────────────────────────────────────────────────────

class ClassNode:
    """create class <name>  (indented body)"""
    def __init__(self, name, body): self.name, self.body = name, body
    def __repr__(self): return f"ClassNode({self.name})"

class CreateObjNode:
    """create <ClassName> as <instance>"""
    def __init__(self, class_name, instance_name):
        self.class_name, self.instance_name = class_name, instance_name
    def __repr__(self): return f"CreateObjNode({self.class_name}, {self.instance_name})"

class InheritClassNode:
    """inherit <child> from <parent>"""
    def __init__(self, child, parent):
        self.child, self.parent = child, parent
    def __repr__(self): return f"InheritClassNode({self.child}, {self.parent})"


# ── File system ───────────────────────────────────────────────────────────────

class ReadNode:
    """read <filename> as <variable>"""
    def __init__(self, filename, variable):
        self.filename, self.variable = filename, variable
    def __repr__(self): return f"ReadNode({self.filename}, {self.variable})"

class WriteNode:
    """write <content> as <filename>"""
    def __init__(self, filename, content):
        self.filename, self.content = filename, content
    def __repr__(self): return f"WriteNode({self.filename}, {self.content})"

class DeleteFileNode:
    """delete file <path>"""
    def __init__(self, path): self.path = path
    def __repr__(self): return f"DeleteFileNode({self.path})"

class MakeDirNode:
    """make folder <path>"""
    def __init__(self, path): self.path = path
    def __repr__(self): return f"MakeDirNode({self.path})"

class ListFilesNode:
    """list files in <path> as <variable>"""
    def __init__(self, path, variable):
        self.path, self.variable = path, variable
    def __repr__(self): return f"ListFilesNode({self.path}, {self.variable})"

class CopyNode:
    """copy <source> as <destination>"""
    def __init__(self, source, destination):
        self.source, self.destination = source, destination
    def __repr__(self): return f"CopyNode({self.source}, {self.destination})"


# ── List / collection helpers ─────────────────────────────────────────────────

class AppendNode:
    """append <value> to <list>"""
    def __init__(self, value, lst): self.value, self.lst = value, lst
    def __repr__(self): return f"AppendNode({self.value}, {self.lst})"

class RemoveNode:
    """remove <value> from <list>"""
    def __init__(self, value, lst): self.value, self.lst = value, lst
    def __repr__(self): return f"RemoveNode({self.value}, {self.lst})"

class CountNode:
    """count <value> in <list> as <variable>"""
    def __init__(self, value, lst, variable):
        self.value, self.lst, self.variable = value, lst, variable
    def __repr__(self): return f"CountNode({self.value}, {self.lst}, {self.variable})"

class SortNode:
    """sort <list>  /  sort <list> descending"""
    def __init__(self, variable, descending=False):
        self.variable, self.descending = variable, descending
    def __repr__(self): return f"SortNode({self.variable}, desc={self.descending})"

class ReverseNode:
    """reverse <list> as <target>"""
    def __init__(self, source, target):
        self.source, self.target = source, target
    def __repr__(self): return f"ReverseNode({self.source}, {self.target})"

class FilterNode:
    """filter <list> where <condition> as <result>"""
    def __init__(self, variable, condition, result):
        self.variable, self.condition, self.result = variable, condition, result
    def __repr__(self): return f"FilterNode({self.variable}, {self.result})"

class MapNode:
    """map <list> with <expression> as <result>"""
    def __init__(self, variable, expression, result):
        self.variable, self.expression, self.result = variable, expression, result
    def __repr__(self): return f"MapNode({self.variable}, {self.result})"

class JoinNode:
    """join <list> with <separator> as <variable>"""
    def __init__(self, lst, separator, variable):
        self.lst, self.separator, self.variable = lst, separator, variable
    def __repr__(self): return f"JoinNode({self.lst}, {self.variable})"

class SplitNode:
    """split <string> by <separator> as <result>"""
    def __init__(self, variable, separator, result):
        self.variable, self.separator, self.result = variable, separator, result
    def __repr__(self): return f"SplitNode({self.variable}, {self.result})"


# ── Math / string helpers ─────────────────────────────────────────────────────

class ConvertNode:
    """convert <variable> to <type>   e.g. convert age to int"""
    def __init__(self, variable, action):
        self.variable, self.action = variable, action
    def __repr__(self): return f"ConvertNode({self.variable}, {self.action})"

class CheckNode:
    """check <left> is <right>   →  type / value check"""
    def __init__(self, left, right): self.left, self.right = left, right
    def __repr__(self): return f"CheckNode({self.left}, {self.right})"


# ── System / environment ──────────────────────────────────────────────────────

class SetEnvNode:
    """set env <KEY> as <value>"""
    def __init__(self, key, value): self.key, self.value = key, value
    def __repr__(self): return f"SetEnvNode({self.key})"

class GetEnvNode:
    """get env <KEY> as <variable>"""
    def __init__(self, key, variable): self.key, self.variable = key, variable
    def __repr__(self): return f"GetEnvNode({self.key}, {self.variable})"

class SleepNode:
    """sleep <seconds>"""
    def __init__(self, seconds): self.seconds = seconds
    def __repr__(self): return f"SleepNode({self.seconds})"

class RunNode:
    """run <shell command>"""
    def __init__(self, command): self.command = command
    def __repr__(self): return f"RunNode({self.command})"

class OSNode:
    """os <component>   e.g. os memory / os cpu / os battery"""
    def __init__(self, component): self.component = component
    def __repr__(self): return f"OSNode({self.component})"

class TaskNode:
    """start <action>   →  run in background thread"""
    def __init__(self, action): self.action = action
    def __repr__(self): return f"TaskNode({self.action})"


# ── Networking ────────────────────────────────────────────────────────────────

class VisitNode:
    """visit <url>   →  open URL in browser"""
    def __init__(self, url): self.url = url
    def __repr__(self): return f"VisitNode({self.url})"

class FetchNode:
    """fetch <url> as <variable>"""
    def __init__(self, url, variable): self.url, self.variable = url, variable
    def __repr__(self): return f"FetchNode({self.url}, {self.variable})"

class PostNode:
    """post <data> to <url> as <variable>"""
    def __init__(self, data, url, variable):
        self.data, self.url, self.variable = data, url, variable
    def __repr__(self): return f"PostNode({self.url}, {self.variable})"

class ConnectSocketNode:
    """connect socket <url>"""
    def __init__(self, url): self.url = url
    def __repr__(self): return f"ConnectSocketNode({self.url})"

class SendSocketNode:
    """send socket <message>"""
    def __init__(self, message): self.message = message
    def __repr__(self): return f"SendSocketNode({self.message})"

class ServeNode:
    """serve on port <port>  /  serve"""
    def __init__(self, port): self.port = port
    def __repr__(self): return f"ServeNode({self.port})"


# ── Database (SQLite / JSON file) ─────────────────────────────────────────────

class OpenDBNode:
    """open database <name>   →  open JSON key-value store"""
    def __init__(self, db_name): self.db_name = db_name
    def __repr__(self): return f"OpenDBNode({self.db_name})"

class SaveDBNode:
    """save <key> as <value>  (into open db)"""
    def __init__(self, entity, value): self.entity, self.value = entity, value
    def __repr__(self): return f"SaveDBNode({self.entity}, {self.value})"

class ConnectDBNode:
    """connect database <type> at <url>"""
    def __init__(self, db_type, url): self.db_type, self.url = db_type, url
    def __repr__(self): return f"ConnectDBNode({self.db_type}, {self.url})"

class QueryDBNode:
    """query <table> where <condition> as <variable>"""
    def __init__(self, table, condition, variable):
        self.table, self.condition, self.variable = table, condition, variable
    def __repr__(self): return f"QueryDBNode({self.table}, {self.variable})"

class DeleteDBNode:
    """delete <key> from database"""
    def __init__(self, key): self.key = key
    def __repr__(self): return f"DeleteDBNode({self.key})"

class CreateTableNode:
    """set <name> as table"""
    def __init__(self, name): self.name = name
    def __repr__(self): return f"CreateTableNode({self.name})"

class AddToTableNode:
    """add <table> "<row data>"""
    def __init__(self, table, row_data): self.table, self.row_data = table, row_data
    def __repr__(self): return f"AddToTableNode({self.table}, {self.row_data})"

class PrintTableNode:
    """print table <name>"""
    def __init__(self, name): self.name = name
    def __repr__(self): return f"PrintTableNode({self.name})"


# ── Crypto / security ─────────────────────────────────────────────────────────

class HashNode:
    """hash <value> as <variable>"""
    def __init__(self, value, variable): self.value, self.variable = value, variable
    def __repr__(self): return f"HashNode({self.value}, {self.variable})"

class EncryptNode:
    """encrypt <variable> with <key> as <result>"""
    def __init__(self, variable, key, result="result"):
        self.variable, self.key, self.result = variable, key, result
    def __repr__(self): return f"EncryptNode({self.variable}, {self.key}, {self.result})"

class DecryptNode:
    """decrypt <variable> with <key> as <result>"""
    def __init__(self, variable, key, result="result"):
        self.variable, self.key, self.result = variable, key, result
    def __repr__(self): return f"DecryptNode({self.variable}, {self.key}, {self.result})"

class LoginNode:
    """login with <provider>"""
    def __init__(self, provider): self.provider = provider
    def __repr__(self): return f"LoginNode({self.provider})"

class LogoutNode:
    """logout"""
    def __repr__(self): return "LogoutNode()"

class SendEmailNode:
    """send email to <to> with subject <subject> and body <body>"""
    def __init__(self, to, subject, body): self.to, self.subject, self.body = to, subject, body
    def __repr__(self): return f"SendEmailNode({self.to})"


# ── PDF / Image ───────────────────────────────────────────────────────────────

class ExportPDFNode:
    """export pdf as <filename>"""
    def __init__(self, filename): self.filename = filename
    def __repr__(self): return f"ExportPDFNode({self.filename})"

class ResizeImageNode:
    """resize image <file> to <width> by <height>"""
    def __init__(self, file, width, height):
        self.file, self.width, self.height = file, width, height
    def __repr__(self): return f"ResizeImageNode({self.file}, {self.width}, {self.height})"


# ── Visualization / utility ───────────────────────────────────────────────────

class ShowChartNode:
    """show chart <type> of <variable>"""
    def __init__(self, chart_type, variable):
        self.chart_type, self.variable = chart_type, variable
    def __repr__(self): return f"ShowChartNode({self.chart_type}, {self.variable})"

class DrawNode:
    """draw <shape> <size>"""
    def __init__(self, shape, size): self.shape, self.size = shape, size
    def __repr__(self): return f"DrawNode({self.shape}, {self.size})"

class MediaNode:
    """media open <file>  /  media chart <variable>"""
    def __init__(self, action, target): self.action, self.target = action, target
    def __repr__(self): return f"MediaNode({self.action}, {self.target})"


# ── Data Science — Pandas / NumPy wrappers ────────────────────────────────────

class LoadDataNode:
    """load data <file_or_url> as <variable>
    Supports: .csv, .json, .xlsx, .parquet"""
    def __init__(self, source, variable, options=None):
        self.source, self.variable = source, variable
        self.options = options or {}
    def __repr__(self): return f"LoadDataNode({self.source}, {self.variable})"

class SaveDataNode:
    """save data <variable> as <file>
    Supports: .csv, .json, .xlsx, .parquet"""
    def __init__(self, variable, file, options=None):
        self.variable, self.file = variable, file
        self.options = options or {}
    def __repr__(self): return f"SaveDataNode({self.variable}, {self.file})"

class ShowDataNode:
    """show data <variable>  [rows <n>]
    Pretty-prints a DataFrame or array."""
    def __init__(self, variable, rows=10):
        self.variable, self.rows = variable, rows
    def __repr__(self): return f"ShowDataNode({self.variable}, rows={self.rows})"

class DescribeDataNode:
    """describe <variable>
    Calls df.describe() and prints statistics."""
    def __init__(self, variable): self.variable = variable
    def __repr__(self): return f"DescribeDataNode({self.variable})"

class SelectColumnsNode:
    """select columns <col1>, <col2>, ... from <df> as <result>"""
    def __init__(self, columns, dataframe, result):
        self.columns, self.dataframe, self.result = columns, dataframe, result
    def __repr__(self): return f"SelectColumnsNode({self.columns}, {self.dataframe}, {self.result})"

class DropColumnsNode:
    """drop columns <col1>, <col2>, ... from <df>"""
    def __init__(self, columns, dataframe):
        self.columns, self.dataframe = columns, dataframe
    def __repr__(self): return f"DropColumnsNode({self.columns}, {self.dataframe})"

class RenameColumnNode:
    """rename column <old> to <new> in <df>"""
    def __init__(self, old_name, new_name, dataframe):
        self.old_name, self.new_name, self.dataframe = old_name, new_name, dataframe
    def __repr__(self): return f"RenameColumnNode({self.old_name} -> {self.new_name})"

class FilterRowsNode:
    """filter rows in <df> where <condition> as <result>"""
    def __init__(self, dataframe, condition, result):
        self.dataframe, self.condition, self.result = dataframe, condition, result
    def __repr__(self): return f"FilterRowsNode({self.dataframe}, {self.result})"

class GroupByNode:
    """group <df> by <column> then <agg_func> <col> as <result>
    e.g. group sales by region then mean revenue as summary"""
    def __init__(self, dataframe, by_col, agg_func, agg_col, result):
        self.dataframe   = dataframe
        self.by_col      = by_col
        self.agg_func    = agg_func   # mean | sum | count | max | min | std
        self.agg_col     = agg_col
        self.result      = result
    def __repr__(self): return f"GroupByNode({self.dataframe}, by={self.by_col}, {self.agg_func})"

class MergeDataNode:
    """merge <df1> with <df2> on <key> as <result>
    Optional: merge ... on <key> how <left|right|inner|outer> as <result>"""
    def __init__(self, df1, df2, on, how, result):
        self.df1, self.df2, self.on, self.how, self.result = df1, df2, on, how, result
    def __repr__(self): return f"MergeDataNode({self.df1}, {self.df2}, on={self.on})"

class FillMissingNode:
    """fill missing in <df> with <value>
    value can be: mean | median | mode | zero | <literal>"""
    def __init__(self, dataframe, value, column=None):
        self.dataframe, self.value, self.column = dataframe, value, column
    def __repr__(self): return f"FillMissingNode({self.dataframe}, {self.value})"

class DropMissingNode:
    """drop missing in <df>"""
    def __init__(self, dataframe): self.dataframe = dataframe
    def __repr__(self): return f"DropMissingNode({self.dataframe})"

class AddColumnNode:
    """add column <name> to <df> as <expression>
    e.g. add column profit to sales as revenue minus cost"""
    def __init__(self, column, dataframe, expression):
        self.column, self.dataframe, self.expression = column, dataframe, expression
    def __repr__(self): return f"AddColumnNode({self.column}, {self.dataframe})"

class NormalizeNode:
    """normalize <df> [column <col>]
    Applies min-max scaling (0-1)."""
    def __init__(self, dataframe, column=None):
        self.dataframe, self.column = dataframe, column
    def __repr__(self): return f"NormalizeNode({self.dataframe}, col={self.column})"

class StandardizeNode:
    """standardize <df> [column <col>]
    Applies z-score standardization."""
    def __init__(self, dataframe, column=None):
        self.dataframe, self.column = dataframe, column
    def __repr__(self): return f"StandardizeNode({self.dataframe}, col={self.column})"

class EncodeNode:
    """encode <df> column <col>
    One-hot encodes a categorical column."""
    def __init__(self, dataframe, column):
        self.dataframe, self.column = dataframe, column
    def __repr__(self): return f"EncodeNode({self.dataframe}, {self.column})"

class SplitDataNode:
    """split <df> into train <train_var> test <test_var> ratio <0.8>
    Splits DataFrame into train/test sets."""
    def __init__(self, dataframe, train_var, test_var, ratio=0.8, target=None):
        self.dataframe  = dataframe
        self.train_var  = train_var
        self.test_var   = test_var
        self.ratio      = ratio
        self.target     = target   # optional: name of label column
    def __repr__(self): return f"SplitDataNode({self.dataframe}, ratio={self.ratio})"

class PlotNode:
    """plot <df_or_var> [as <chart_type>] [title <text>] [x <col>] [y <col>]
    chart_type: line | bar | scatter | histogram | heatmap | box | pie"""
    def __init__(self, variable, chart_type="line", title="", x_col=None, y_col=None, save_as=None):
        self.variable   = variable
        self.chart_type = chart_type
        self.title      = title
        self.x_col      = x_col
        self.y_col      = y_col
        self.save_as    = save_as   # if given, save to file instead of show
    def __repr__(self): return f"PlotNode({self.variable}, {self.chart_type})"

class StatsNode:
    """stats <variable> as <result>
    Returns dict with mean, median, std, min, max, count."""
    def __init__(self, variable, result):
        self.variable, self.result = variable, result
    def __repr__(self): return f"StatsNode({self.variable}, {self.result})"


# ── Machine Learning — local (scikit-learn) ───────────────────────────────────

class CreateModelNode:
    """create model <type> as <name>
    type: linear | logistic | tree | forest | svm | knn | naive_bayes |
          kmeans | dbscan | pca | gradient_boost | xgboost | ridge | lasso
    All run locally via scikit-learn — no API needed."""
    def __init__(self, model_type, name, params=None):
        self.model_type = model_type
        self.name       = name
        self.params     = params or {}   # e.g. {"n_estimators": 100}
    def __repr__(self): return f"CreateModelNode({self.model_type}, {self.name})"

class SetParamNode:
    """set param <model> <param> as <value>
    e.g. set param forest n_estimators as 200"""
    def __init__(self, model, param, value):
        self.model, self.param, self.value = model, param, value
    def __repr__(self): return f"SetParamNode({self.model}, {self.param}={self.value})"

class TrainModelNode:
    """train <model> on <df> predict <target_col>
    Optional: train ... features <col1> <col2> ...
    Fits the sklearn model on X/y split from DataFrame."""
    def __init__(self, model, dataframe, target, features=None):
        self.model, self.dataframe, self.target = model, dataframe, target
        self.features = features   # list of column names; None = all except target
    def __repr__(self): return f"TrainModelNode({self.model}, {self.dataframe})"

class EvaluateModelNode:
    """evaluate <model> on <df> as <result>
    Returns accuracy / RMSE / silhouette score into <result>."""
    def __init__(self, model, dataframe, result, target=None, metric=None):
        self.model, self.dataframe, self.result = model, dataframe, result
        self.target = target
        self.metric = metric   # accuracy | rmse | r2 | f1 | silhouette
    def __repr__(self): return f"EvaluateModelNode({self.model}, {self.result})"

class PredictNode:
    """predict using <model> on <df_or_var> as <result>
    Runs model.predict() and stores output."""
    def __init__(self, model, source, result):
        self.model, self.source, self.result = model, source, result
    def __repr__(self): return f"PredictNode({self.model}, {self.result})"

class SaveModelNode:
    """save model <name> as <file>
    Serialises with joblib (sklearn) or torch.save (neural nets)."""
    def __init__(self, name, file): self.name, self.file = name, file
    def __repr__(self): return f"SaveModelNode({self.name}, {self.file})"

class LoadModelNode:
    """load model <file> as <name>"""
    def __init__(self, file, name): self.file, self.name = file, name
    def __repr__(self): return f"LoadModelNode({self.file}, {self.name})"

class TuneModelNode:
    """tune <model> on <df> predict <target> trials <n> as <result>
    Grid-search / random-search over default param grid."""
    def __init__(self, model, dataframe, target, trials, result):
        self.model, self.dataframe, self.target = model, dataframe, target
        self.trials, self.result = trials, result
    def __repr__(self): return f"TuneModelNode({self.model}, trials={self.trials})"

class CrossValidateNode:
    """cross validate <model> on <df> predict <target> folds <k> as <result>"""
    def __init__(self, model, dataframe, target, folds, result):
        self.model, self.dataframe, self.target = model, dataframe, target
        self.folds, self.result = folds, result
    def __repr__(self): return f"CrossValidateNode({self.model}, folds={self.folds})"

class FeatureImportanceNode:
    """feature importance of <model> as <result>"""
    def __init__(self, model, result): self.model, self.result = model, result
    def __repr__(self): return f"FeatureImportanceNode({self.model}, {self.result})"

class ConfusionMatrixNode:
    """confusion matrix of <model> on <df> as <result>"""
    def __init__(self, model, dataframe, result, target=None):
        self.model, self.dataframe, self.result = model, dataframe, result
        self.target = target
    def __repr__(self): return f"ConfusionMatrixNode({self.model}, {self.result})"


# ── Deep Learning — PyTorch ───────────────────────────────────────────────────

class CreateNetworkNode:
    """create network <name> layers <l1>, <l2>, ... [activation <func>]
    Builds a simple fully-connected PyTorch network.
    activation: relu | tanh | sigmoid | leaky_relu"""
    def __init__(self, name, layers, activation="relu", output_activation=None):
        self.name             = name
        self.layers           = layers          # list of ints, e.g. [128, 64, 10]
        self.activation       = activation
        self.output_activation = output_activation  # softmax | sigmoid | None
    def __repr__(self): return f"CreateNetworkNode({self.name}, {self.layers})"

class TrainNetworkNode:
    """train network <name> on <df> predict <target>
       epochs <n> batch <b> lr <learning_rate> [loss <func>] [optimizer <opt>]
    loss: mse | cross_entropy | binary_cross_entropy | mae
    optimizer: adam | sgd | rmsprop | adagrad"""
    def __init__(self, name, dataframe, target, epochs=10, batch=32,
                 lr=0.001, loss="mse", optimizer="adam", features=None):
        self.name       = name
        self.dataframe  = dataframe
        self.target     = target
        self.epochs     = epochs
        self.batch      = batch
        self.lr         = lr
        self.loss       = loss
        self.optimizer  = optimizer
        self.features   = features
    def __repr__(self): return f"TrainNetworkNode({self.name}, epochs={self.epochs})"

class PredictNetworkNode:
    """predict using network <name> on <source> as <result>"""
    def __init__(self, name, source, result):
        self.name, self.source, self.result = name, source, result
    def __repr__(self): return f"PredictNetworkNode({self.name}, {self.result})"

class SaveNetworkNode:
    """save network <name> as <file>"""
    def __init__(self, name, file): self.name, self.file = name, file
    def __repr__(self): return f"SaveNetworkNode({self.name}, {self.file})"

class LoadNetworkNode:
    """load network <file> as <name>"""
    def __init__(self, file, name): self.file, self.name = file, name
    def __repr__(self): return f"LoadNetworkNode({self.file}, {self.name})"

class SetLossNode:
    """set loss of <network> as <loss_func>"""
    def __init__(self, network, loss): self.network, self.loss = network, loss
    def __repr__(self): return f"SetLossNode({self.network}, {self.loss})"

class SetOptimizerNode:
    """set optimizer of <network> as <optimizer> [lr <rate>]"""
    def __init__(self, network, optimizer, lr=0.001):
        self.network, self.optimizer, self.lr = network, optimizer, lr
    def __repr__(self): return f"SetOptimizerNode({self.network}, {self.optimizer})"


# ── LLM — local only (llama.cpp / HuggingFace transformers) ──────────────────

class LoadLLMNode:
    """load llm <model_path_or_name> as <variable>
    Loads a local LLM:
      - HuggingFace model id  →  uses transformers (AutoModelForCausalLM)
      - .gguf file path       →  uses llama-cpp-python
    No cloud API used. Model runs entirely on your hardware."""
    def __init__(self, source, variable, options=None):
        self.source, self.variable = source, variable
        self.options = options or {}   # max_tokens, temperature, n_gpu_layers ...
    def __repr__(self): return f"LoadLLMNode({self.source}, {self.variable})"

class PromptLLMNode:
    """prompt <llm_var> with <text> as <result>
    Runs inference locally. Result stored in <result>."""
    def __init__(self, llm_var, prompt, result, options=None):
        self.llm_var, self.prompt, self.result = llm_var, prompt, result
        self.options = options or {}   # max_tokens, temperature, top_p ...
    def __repr__(self): return f"PromptLLMNode({self.llm_var}, {self.result})"

class SetLLMParamNode:
    """set llm param <llm_var> <param> as <value>
    e.g. set llm param mybot temperature as 0.7"""
    def __init__(self, llm_var, param, value):
        self.llm_var, self.param, self.value = llm_var, param, value
    def __repr__(self): return f"SetLLMParamNode({self.llm_var}, {self.param}={self.value})"

class FineTuneLLMNode:
    """fine tune <llm_var> on <df> input <col> output <col> epochs <n>
    Fine-tunes a HuggingFace model using the dataset DataFrame."""
    def __init__(self, llm_var, dataframe, input_col, output_col, epochs=3, lr=2e-5):
        self.llm_var   = llm_var
        self.dataframe = dataframe
        self.input_col = input_col
        self.output_col = output_col
        self.epochs    = epochs
        self.lr        = lr
    def __repr__(self): return f"FineTuneLLMNode({self.llm_var}, epochs={self.epochs})"


# ── Computer Vision — local (OpenCV / torchvision) ───────────────────────────

class LoadImageNode:
    """load image <file> as <variable>"""
    def __init__(self, file, variable): self.file, self.variable = file, variable
    def __repr__(self): return f"LoadImageNode({self.file}, {self.variable})"

class ShowImageNode:
    """show image <variable>"""
    def __init__(self, variable): self.variable = variable
    def __repr__(self): return f"ShowImageNode({self.variable})"

class SaveImageNode:
    """save image <variable> as <file>"""
    def __init__(self, variable, file): self.variable, self.file = variable, file
    def __repr__(self): return f"SaveImageNode({self.variable}, {self.file})"

class ResizeImageCVNode:
    """resize image <variable> to <width> <height> as <result>"""
    def __init__(self, variable, width, height, result):
        self.variable, self.width, self.height, self.result = variable, width, height, result
    def __repr__(self): return f"ResizeImageCVNode({self.variable}, {self.width}x{self.height})"

class GrayscaleNode:
    """grayscale <variable> as <result>"""
    def __init__(self, variable, result): self.variable, self.result = variable, result
    def __repr__(self): return f"GrayscaleNode({self.variable}, {self.result})"

class DetectObjectsNode:
    """detect objects in <variable> as <result> [model <model_var>]
    Uses a local YOLO or torchvision detection model."""
    def __init__(self, variable, result, model=None):
        self.variable, self.result, self.model = variable, result, model
    def __repr__(self): return f"DetectObjectsNode({self.variable}, {self.result})"

class ClassifyImageNode:
    """classify image <variable> using <model_var> as <result>"""
    def __init__(self, variable, model, result):
        self.variable, self.model, self.result = variable, model, result
    def __repr__(self): return f"ClassifyImageNode({self.variable}, {self.result})"

class LoadVideoNode:
    """load video <file_or_cam> as <variable>
    file_or_cam: file path or '0' for webcam."""
    def __init__(self, source, variable): self.source, self.variable = source, variable
    def __repr__(self): return f"LoadVideoNode({self.source}, {self.variable})"

class CaptureFrameNode:
    """capture frame from <video_var> as <result>"""
    def __init__(self, video_var, result): self.video_var, self.result = video_var, result
    def __repr__(self): return f"CaptureFrameNode({self.video_var}, {self.result})"

class ApplyFilterNode:
    """apply filter <filter_name> to <variable> as <result>
    filter_name: blur | sharpen | edge | brightness | contrast"""
    def __init__(self, filter_name, variable, result, strength=1.0):
        self.filter_name, self.variable, self.result = filter_name, variable, result
        self.strength = strength
    def __repr__(self): return f"ApplyFilterNode({self.filter_name}, {self.variable})"

class AugmentImageNode:
    """augment <variable> with <ops> as <result>
    ops: flip | rotate | crop | noise | zoom (comma-separated)"""
    def __init__(self, variable, ops, result):
        self.variable, self.ops, self.result = variable, ops, result
    def __repr__(self): return f"AugmentImageNode({self.variable}, {self.ops})"


# ── Audio — local (librosa / sounddevice / torchaudio) ───────────────────────

class LoadAudioNode:
    """load audio <file> as <variable>"""
    def __init__(self, file, variable): self.file, self.variable = file, variable
    def __repr__(self): return f"LoadAudioNode({self.file}, {self.variable})"

class PlayAudioNode:
    """play audio <variable>"""
    def __init__(self, variable): self.variable = variable
    def __repr__(self): return f"PlayAudioNode({self.variable})"

class SaveAudioNode:
    """save audio <variable> as <file>"""
    def __init__(self, variable, file): self.variable, self.file = variable, file
    def __repr__(self): return f"SaveAudioNode({self.variable}, {self.file})"

class RecordAudioNode:
    """record audio <seconds> as <variable>"""
    def __init__(self, seconds, variable): self.seconds, self.variable = seconds, variable
    def __repr__(self): return f"RecordAudioNode({self.seconds}s, {self.variable})"

class TranscribeAudioNode:
    """transcribe <audio_var> as <result>  [model <model_name>]
    Uses local Whisper (openai-whisper package) — no API."""
    def __init__(self, audio_var, result, model="base"):
        self.audio_var, self.result, self.model = audio_var, result, model
    def __repr__(self): return f"TranscribeAudioNode({self.audio_var}, {self.result})"

class AudioFeaturesNode:
    """audio features of <variable> as <result>
    Extracts MFCC, spectrogram, zero-crossing rate via librosa."""
    def __init__(self, variable, result): self.variable, self.result = variable, result
    def __repr__(self): return f"AudioFeaturesNode({self.variable}, {self.result})"


# ── Generative — local only ───────────────────────────────────────────────────

class GenerateImageNode:
    """generate image <prompt> as <variable> [model <model_name>]
    Uses local Stable Diffusion (diffusers). No cloud API."""
    def __init__(self, prompt, variable, model="stabilityai/stable-diffusion-2-1",
                 width=512, height=512, steps=30):
        self.prompt, self.variable, self.model = prompt, variable, model
        self.width, self.height, self.steps = width, height, steps
    def __repr__(self): return f"GenerateImageNode({self.variable})"

class TextToSpeechNode:
    """speak <text> as <file>  [voice <voice>]
    Uses local TTS (pyttsx3 or TTS library). No cloud API."""
    def __init__(self, text, file=None, voice=None):
        self.text, self.file, self.voice = text, file, voice
    def __repr__(self): return f"TextToSpeechNode({self.text})"


# ── NLP helpers — local (spaCy / NLTK / transformers) ────────────────────────

class TokenizeTextNode:
    """tokenize <variable> as <result>"""
    def __init__(self, variable, result): self.variable, self.result = variable, result
    def __repr__(self): return f"TokenizeTextNode({self.variable}, {self.result})"

class SentimentNode:
    """sentiment of <variable> as <result>
    Uses local VADER or transformers pipeline."""
    def __init__(self, variable, result): self.variable, self.result = variable, result
    def __repr__(self): return f"SentimentNode({self.variable}, {self.result})"

class EmbedTextNode:
    """embed <variable> using <model_var> as <result>
    Returns a numpy vector."""
    def __init__(self, variable, model, result):
        self.variable, self.model, self.result = variable, model, result
    def __repr__(self): return f"EmbedTextNode({self.variable}, {self.result})"

class SummarizeTextNode:
    """summarize <variable> as <result>  [max words <n>]
    Uses local transformers summarization pipeline."""
    def __init__(self, variable, result, max_words=100):
        self.variable, self.result, self.max_words = variable, result, max_words
    def __repr__(self): return f"SummarizeTextNode({self.variable}, {self.result})"

class TranslateTextNode:
    """translate <variable> to <language> as <result>
    Uses local Helsinki-NLP/opus-mt model."""
    def __init__(self, variable, language, result):
        self.variable, self.language, self.result = variable, language, result
    def __repr__(self): return f"TranslateTextNode({self.variable}, {self.language})"
