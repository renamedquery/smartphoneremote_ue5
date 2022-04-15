def printTraceback(ex):
    trace = []
    tb = ex.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    print(str({
        'type': type(ex).__name__,
        'message': str(ex),
        'trace': trace
    }))