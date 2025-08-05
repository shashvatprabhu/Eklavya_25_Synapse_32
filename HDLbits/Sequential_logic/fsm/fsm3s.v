//

module top_module(
    input clk,
    input in,
    input reset,
    output out); //
    parameter A = 2'b00, B = 2'b01, C = 2'b10, D = 2'b11;
    reg [1:0] next_state,state;
    // State transition logic
    always @(*) begin
        case (state)
            A: next_state = in ? B : A;
            B: next_state = in ? B : C;
            C: next_state = in ? D : A;
            D: next_state = in ? B : C;
            default: next_state = A;
        endcase
    end
    // State flip-flops with synchronous reset
    always @(posedge clk) begin
        // State flip-flops with synchronous reset
        if (reset)
            state <= A;
        else
            state <= next_state;
    end
    // Output logic
    always @(*) begin
        case (state)
            D: out = 1;
            default: out = 0;
        endcase
    end
endmodule