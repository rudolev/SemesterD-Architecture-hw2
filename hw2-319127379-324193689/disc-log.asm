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
    push rbx
    sub rsp, 40
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

    ; Output calculations after format
    movsd xmm3, xmm0
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
; compute_log: Compute the log given the base, num, and epsilon.
; -----------------------------------------------------------------------------
compute_log:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    
    movsd [rbp - 8], xmm0
    movsd [rbp - 16], xmm1
    movsd [rbp - 24], xmm2  ; eps

    ; Base Case: If b <= 1.0 (or within epsilon distance of 1.0), return 0
    movsd xmm3, [float_one]
    comisd xmm1, xmm3
    jbe .return_zero

    ; --- Case 1: If a > b ---
    comisd xmm0, xmm1
    ja .case_greater

    ; --- Case 2: else, if b/a < (1.0 + eps) ---
    movsd xmm0, xmm1
    divsd xmm0, [rbp - 8]
    
    ; Add safeguard: if b/a is 1.0, stop recursion loop
    movsd xmm3, [float_one]
    addsd xmm3, [rbp - 24]
    comisd xmm0, xmm3
    jbe .case_epsilon_reached

    ; --- Case 3: else, return 1 + log_a(b / a) ---
    movsd xmm0, [rbp - 8]
    movsd xmm1, [rbp - 16]  
    divsd xmm1, xmm0
    movsd xmm2, [rbp - 24]  
    call compute_log        
    
    addsd xmm0, [float_one] 
    jmp .done

.case_greater:
    ; return 1.0 / log_b(a)
    movsd xmm0, [rbp - 16]
    movsd xmm1, [rbp - 8]
    movsd xmm2, [rbp - 24]  
    call compute_log        
    
    movsd xmm1, [float_one]
    divsd xmm1, xmm0
    movsd xmm0, xmm1
    jmp .done

.case_epsilon_reached:
    movsd xmm0, [float_one] 
    jmp .done

.return_zero:
    xorpd xmm0, xmm0

.done:
    leave
    ret