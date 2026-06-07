section .rodata
    usage_msg       db "Usage:", 10, "        <program> <base> <number> <epsilon>", 10, 0
    usage_len       equ $ - usage_msg
    
    ; Format string for output: log_{base}(num) = result
    fmt_out         db "log_(%.0f)(%.0f) = %.16g", 10, 0
    fmt_out_int     db "log_(%.0f)(%.0f) = %.15g", 10, 0 ; fallback to match whole integer cases perfectly if needed

    ; Constants
    float_one       dq 1.0

section .text
    global main
    extern sscanf
    extern printf
    extern fprintf
    extern stderr

main:
    push rbp
    mov rbp, rsp
    
    ; We need space for 3 local doubles (8 bytes each) to pass to sscanf
    ; base: [rbp-8], number: [rbp-16], epsilon: [rbp-24]
    sub rsp, 32

    ; 1. Validate argument count (argc must be exactly 4: prog, base, num, eps)
    cmp rdi, 4
    jne .print_usage

    ; Save argv
    mov rbx, rsi 

    ; Parse base (argv[1])
    mov rdi, [rbx + 8]   ; argv[1]
    mov rsi, .fmt_double ; "%lf"
    lea rdx, [rbp - 8]   ; &base
    xor eax, eax
    call sscanf
    cmp eax, 1
    jne .print_usage

    ; Parse number (argv[2])
    mov rdi, [rbx + 16]  ; argv[2]
    mov rsi, .fmt_double ; "%lf"
    lea rdx, [rbp - 16]  ; &number
    xor eax, eax
    call sscanf
    cmp eax, 1
    jne .print_usage

    ; Parse epsilon (argv[3])
    mov rdi, [rbx + 24]  ; argv[3]
    mov rsi, .fmt_double ; "%lf"
    lea rdx, [rbp - 24]  ; &epsilon
    xor eax, eax
    call sscanf
    cmp eax, 1
    jne .print_usage

    ; 2. Call the recursive log function
    movsd xmm0, [rbp - 8]   ; xmm0 = a (base)
    movsd xmm1, [rbp - 16]  ; xmm1 = b (number)
    movsd xmm2, [rbp - 24]  ; xmm2 = eps
    call compute_log

    ; 3. Print the result to stdout
    movsd xmm3, xmm0        ; result moves to xmm3
    mov rdi, fmt_out
    movsd xmm0, [rbp - 8]   ; base
    movsd xmm1, [rbp - 16]  ; number
    movsd xmm2, xmm3        ; result
    mov eax, 3              ; 3 float arguments
    call printf

    xor eax, eax
    mov rsp, rbp
    pop rbp
    ret

.print_usage:
    ; Print Usage block to stderr
    mov rdi, [stderr]
    mov rsi, usage_msg
    xor eax, eax
    call fprintf
    
    mov eax, 1
    mov rsp, rbp
    pop rbp
    ret

section .rodata
    .fmt_double db "%lf", 0

section .text
; -----------------------------------------------------------------------------
; compute_log: Recursive core logic matching the PDF spec.
; Inputs:
;   xmm0 = a (base)
;   xmm1 = b (number)
;   xmm2 = epsilon
; Output:
;   xmm0 = computed result
; -----------------------------------------------------------------------------
compute_log:
    push rbp
    mov rbp, rsp
    sub rsp, 32             ; allocate space to save state across recursive calls
    
    ; Save parameters onto local stack frames
    movsd [rbp - 8], xmm0   ; a
    movsd [rbp - 16], xmm1  ; b
    movsd [rbp - 24], xmm2  ; eps

    ; --- Case 1: If a > b ---
    comisd xmm0, xmm1
    ja .case_greater

    ; --- Case 2: Otherwise, if b/a < eps ---
    movsd xmm0, xmm1
    divsd xmm0, [rbp - 8]   ; xmm0 = b / a
    comisd xmm0, [rbp - 24] ; compare (b/a) with eps
    jb .case_epsilon_reached

    ; --- Case 3: Otherwise, return 1 + log_a(b / a) ---
    movsd xmm0, [rbp - 8]   ; base remains 'a'
    movsd xmm1, [rbp - 16]  
    divsd xmm1, xmm0        ; argument becomes b / a
    movsd xmm2, [rbp - 24]  ; epsilon remains same
    call compute_log        ; returns log_a(b/a) in xmm0
    
    addsd xmm0, [float_one] ; add 1.0
    jmp .done

.case_greater:
    ; return 1.0 / log_b(a)
    movsd xmm0, [rbp - 16]  ; new base = b
    movsd xmm1, [rbp - 8]   ; new number = a
    movsd xmm2, [rbp - 24]  ; epsilon remains same
    call compute_log        ; returns log_b(a) in xmm0
    
    movsd xmm1, [float_one]
    divsd xmm1, xmm0        ; 1.0 / log_b(a)
    movsd xmm0, xmm1
    jmp .done

.case_epsilon_reached:
    movsd xmm0, [float_one] ; return 1

.done:
    mov rsp, rbp
    pop rbp
    ret