from llvmlite import ir

mod=ir.Module(name="hello_module")
int_type = ir.IntType(32)
hello_func = ir.Function(mod, ir.FunctionType(int_type, []), name="hello_func")
block=hello_func.append_basic_block("entry")
builder = ir.IRBuilder(block)
builder.ret(ir.Constant(ir.IntType(32), 42))

print(mod)
