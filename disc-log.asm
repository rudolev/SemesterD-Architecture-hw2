section .rodata
    usage_msg       db "Usage:", 10, "        <program> <base> <number> <epsilon>", 10, 0
    fmt_out         db "log_(%.0f)(%.0f) = %.16g", 10, 0
    fmt_double      db "%lf", 0
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
    push rbx                ; Save callee-saved register
    sub rsp, 40             ; Allocation space for local variables (16-byte aligned)
                            ; [rbp-16] = saved rbx
                            ; [rbp-24] = base (double)
                            ; [rbp-32] = number (double)
                            ; [rbp-40] = epsilon (double)

    ; Validate argument count (argc must be exactly 4)
    cmp rdi, 4
    jne .print_usage

    mov rbx, rsi            ; Save argv string array pointer

    ; Parse base
    mov rdi, [rbx + 8]      
    mov rsi, fmt_double     
    lea rdx, [rbp - 24]     
    xor eax, eax
    call sscanf
    cmp eax, 1
    jne .print_usage

    ; Parse number
    mov rdi, [rbx + 16]     
    mov rsi, fmt_double     
    lea rdx, [rbp - 32]     
    xor eax, eax
    call sscanf
    cmp eax, 1
    jne .print_usage

    ; Parse epsilon
    mov rdi, [rbx + 24]     
    mov rsi, fmt_double     
    lea rdx, [rbp - 40]     
    xor eax, eax
    call sscanf
    cmp eax, 1
    jne .print_usage

    ; Execute core calculation
    movsd xmm0, [rbp - 24]  ; base (a)
    movsd xmm1, [rbp - 32]  ; number (b)
    movsd xmm2, [rbp - 40]  ; epsilon
    call compute_log

    ; Output formatted calculations
    movsd xmm3, xmm0        ; Temp swap calculation result to safety
    mov rdi, fmt_out
    movsd xmm0, [rbp - 24]  ; original base
    movsd xmm1, [rbp - 32]  ; original number
    movsd xmm2, xmm3        ; result
    mov eax, 3              ; 3 vector float arguments populated
    call printf

    xor eax, eax
    jmp .exit

.print_usage:
    mov rdi, [stderr]
    mov rsi, usage_msg
    xor eax, eax
    call fprintf
    mov eax, 1

.exit:
    add rsp, 40
    pop rbx
    pop rbp
    ret

; -----------------------------------------------------------------------------
; compute_log: Corrected Base Evaluation Framework
; -----------------------------------------------------------------------------
compute_log:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    
    movsd [rbp - 8], xmm0   ; a
    movsd [rbp - 16], xmm1  ; b
    movsd [rbp - 24], xmm2  ; eps

    ; Base Case Guard: If b <= 1.0 (or within epsilon distance of 1.0), return 0
    movsd xmm3, [float_one]
    comisd xmm1, xmm3
    jbe .return_zero

    ; --- Case 1: If a > b ---
    comisd xmm0, xmm1
    ja .case_greater

    ; --- Case 2: Otherwise, if b/a < (1.0 + eps) ---
    movsd xmm0, xmm1
    divsd xmm0, [rbp - 8]   ; xmm0 = b / a
    
    ; Add termination safeguard: if b/a is basically 1.0, stop recursion loop
    movsd xmm3, [float_one]
    addsd xmm3, [rbp - 24]  ; 1.0 + eps
    comisd xmm0, xmm3
    jbe .case_epsilon_reached

    ; --- Case 3: Otherwise, return 1 + log_a(b / a) ---
    movsd xmm0, [rbp - 8]   ; structural base 'a' remains unchanged
    movsd xmm1, [rbp - 16]  
    divsd xmm1, xmm0        ; reduce parameters: new b = b / a
    movsd xmm2, [rbp - 24]  
    call compute_log        
    
    addsd xmm0, [float_one] 
    jmp .done

.case_greater:
    ; return 1.0 / log_b(a)
    movsd xmm0, [rbp - 16]  ; inverted base = b
    movsd xmm1, [rbp - 8]   ; inverted target = a
    movsd xmm2, [rbp - 24]  
    call compute_log        
    
    movsd xmm1, [float_one]
    divsd xmm1, xmm0        ; 1.0 / log_b(a)
    movsd xmm0, xmm1
    jmp .done

.case_epsilon_reached:
    movsd xmm0, [float_one] 
    jmp .done

.return_zero:
    xorpd xmm0, xmm0        ; clean register to return absolute 0.0 value

.done:
    leave
    ret