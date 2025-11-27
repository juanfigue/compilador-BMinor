; ModuleID = "bminor"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare void @"_printi"(i32 %".1")

declare void @"_prints"(i8* %".1")

declare void @"_printb"(i1 %".1")

declare void @"_printf"(double %".1")

declare void @"_printc"(i8 %".1")

@"SIZE" = global i32 9
@"matA" = global [9 x i32] [i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0]
@"matB" = global [9 x i32] [i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0]
@"matC" = global [9 x i32] [i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0, i32 0]
define void @"main"()
{
entry:
  %"i" = alloca i32
  %".2" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 0
  store i32 1, i32* %".2"
  %".4" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 1
  store i32 2, i32* %".4"
  %".6" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 2
  store i32 3, i32* %".6"
  %".8" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 3
  store i32 4, i32* %".8"
  %".10" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 4
  store i32 5, i32* %".10"
  %".12" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 5
  store i32 6, i32* %".12"
  %".14" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 6
  store i32 7, i32* %".14"
  %".16" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 7
  store i32 8, i32* %".16"
  %".18" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 8
  store i32 9, i32* %".18"
  %".20" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 0
  store i32 9, i32* %".20"
  %".22" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 1
  store i32 8, i32* %".22"
  %".24" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 2
  store i32 7, i32* %".24"
  %".26" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 3
  store i32 6, i32* %".26"
  %".28" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 4
  store i32 5, i32* %".28"
  %".30" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 5
  store i32 4, i32* %".30"
  %".32" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 6
  store i32 3, i32* %".32"
  %".34" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 7
  store i32 2, i32* %".34"
  %".36" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 8
  store i32 1, i32* %".36"
  %".38" = bitcast [11 x i8]* @".str.0" to i8*
  %".39" = bitcast [11 x i8]* @".str.0" to i8*
  call void @"_prints"(i8* %".39")
  store i32 0, i32* %"i"
  br label %"for_cond"
for_cond:
  %".43" = load i32, i32* %"i"
  %".44" = load i32, i32* @"SIZE"
  %".45" = icmp slt i32 %".43", %".44"
  br i1 %".45", label %"for_body", label %"for_end"
for_body:
  %".47" = load i32, i32* %"i"
  %".48" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 %".47"
  %".49" = load i32, i32* %".48"
  call void @"_printi"(i32 %".49")
  %".51" = bitcast [2 x i8]* @".str.1" to i8*
  %".52" = bitcast [2 x i8]* @".str.1" to i8*
  call void @"_prints"(i8* %".52")
  %".54" = load i32, i32* %"i"
  %".55" = add i32 %".54", 1
  %".56" = srem i32 %".55", 3
  %".57" = icmp eq i32 %".56", 0
  br i1 %".57", label %"if_then", label %"if_end"
for_update:
  %".65" = load i32, i32* %"i"
  %".66" = add i32 %".65", 1
  store i32 %".66", i32* %"i"
  br label %"for_cond"
for_end:
  %".69" = bitcast [12 x i8]* @".str.3" to i8*
  %".70" = bitcast [12 x i8]* @".str.3" to i8*
  call void @"_prints"(i8* %".70")
  store i32 0, i32* %"i"
  br label %"for_cond.1"
if_then:
  %".59" = bitcast [2 x i8]* @".str.2" to i8*
  %".60" = bitcast [2 x i8]* @".str.2" to i8*
  call void @"_prints"(i8* %".60")
  br label %"if_end"
if_else:
  br label %"if_end"
if_end:
  br label %"for_update"
for_cond.1:
  %".74" = load i32, i32* %"i"
  %".75" = load i32, i32* @"SIZE"
  %".76" = icmp slt i32 %".74", %".75"
  br i1 %".76", label %"for_body.1", label %"for_end.1"
for_body.1:
  %".78" = load i32, i32* %"i"
  %".79" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 %".78"
  %".80" = load i32, i32* %".79"
  call void @"_printi"(i32 %".80")
  %".82" = bitcast [2 x i8]* @".str.1" to i8*
  %".83" = bitcast [2 x i8]* @".str.1" to i8*
  call void @"_prints"(i8* %".83")
  %".85" = load i32, i32* %"i"
  %".86" = add i32 %".85", 1
  %".87" = srem i32 %".86", 3
  %".88" = icmp eq i32 %".87", 0
  br i1 %".88", label %"if_then.1", label %"if_end.1"
for_update.1:
  %".96" = load i32, i32* %"i"
  %".97" = add i32 %".96", 1
  store i32 %".97", i32* %"i"
  br label %"for_cond.1"
for_end.1:
  store i32 0, i32* %"i"
  br label %"for_cond.2"
if_then.1:
  %".90" = bitcast [2 x i8]* @".str.2" to i8*
  %".91" = bitcast [2 x i8]* @".str.2" to i8*
  call void @"_prints"(i8* %".91")
  br label %"if_end.1"
if_else.1:
  br label %"if_end.1"
if_end.1:
  br label %"for_update.1"
for_cond.2:
  %".102" = load i32, i32* %"i"
  %".103" = load i32, i32* @"SIZE"
  %".104" = icmp slt i32 %".102", %".103"
  br i1 %".104", label %"for_body.2", label %"for_end.2"
for_body.2:
  %".106" = load i32, i32* %"i"
  %".107" = getelementptr [9 x i32], [9 x i32]* @"matA", i32 0, i32 %".106"
  %".108" = load i32, i32* %".107"
  %".109" = load i32, i32* %"i"
  %".110" = getelementptr [9 x i32], [9 x i32]* @"matB", i32 0, i32 %".109"
  %".111" = load i32, i32* %".110"
  %".112" = add i32 %".108", %".111"
  %".113" = load i32, i32* %"i"
  %".114" = getelementptr [9 x i32], [9 x i32]* @"matC", i32 0, i32 %".113"
  store i32 %".112", i32* %".114"
  br label %"for_update.2"
for_update.2:
  %".117" = load i32, i32* %"i"
  %".118" = add i32 %".117", 1
  store i32 %".118", i32* %"i"
  br label %"for_cond.2"
for_end.2:
  %".121" = bitcast [20 x i8]* @".str.4" to i8*
  %".122" = bitcast [20 x i8]* @".str.4" to i8*
  call void @"_prints"(i8* %".122")
  store i32 0, i32* %"i"
  br label %"for_cond.3"
for_cond.3:
  %".126" = load i32, i32* %"i"
  %".127" = load i32, i32* @"SIZE"
  %".128" = icmp slt i32 %".126", %".127"
  br i1 %".128", label %"for_body.3", label %"for_end.3"
for_body.3:
  %".130" = load i32, i32* %"i"
  %".131" = getelementptr [9 x i32], [9 x i32]* @"matC", i32 0, i32 %".130"
  %".132" = load i32, i32* %".131"
  call void @"_printi"(i32 %".132")
  %".134" = bitcast [2 x i8]* @".str.1" to i8*
  %".135" = bitcast [2 x i8]* @".str.1" to i8*
  call void @"_prints"(i8* %".135")
  %".137" = load i32, i32* %"i"
  %".138" = add i32 %".137", 1
  %".139" = srem i32 %".138", 3
  %".140" = icmp eq i32 %".139", 0
  br i1 %".140", label %"if_then.2", label %"if_end.2"
for_update.3:
  %".148" = load i32, i32* %"i"
  %".149" = add i32 %".148", 1
  store i32 %".149", i32* %"i"
  br label %"for_cond.3"
for_end.3:
  ret void
if_then.2:
  %".142" = bitcast [2 x i8]* @".str.2" to i8*
  %".143" = bitcast [2 x i8]* @".str.2" to i8*
  call void @"_prints"(i8* %".143")
  br label %"if_end.2"
if_else.2:
  br label %"if_end.2"
if_end.2:
  br label %"for_update.3"
}

@".str.0" = constant [11 x i8] c"Matriz A:\0a\00"
@".str.1" = constant [2 x i8] c" \00"
@".str.2" = constant [2 x i8] c"\0a\00"
@".str.3" = constant [12 x i8] c"\0aMatriz B:\0a\00"
@".str.4" = constant [20 x i8] c"\0aMatriz C (A + B):\0a\00"