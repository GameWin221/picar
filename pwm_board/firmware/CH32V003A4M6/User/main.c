#include "debug.h"

#define SDA_PIN GPIO_Pin_2
#define SCL_PIN GPIO_Pin_1

#define CH1_PIN GPIO_Pin_6
#define CH2_PIN GPIO_Pin_7
#define CH3_PIN GPIO_Pin_6
#define CH4_PIN GPIO_Pin_5

#define CH1_PIN_TYPE GPIOC
#define CH2_PIN_TYPE GPIOC
#define CH3_PIN_TYPE GPIOD
#define CH4_PIN_TYPE GPIOD

#define CHANNEL_PINS_ON_GPIOD (CH3_PIN | CH4_PIN)
#define CHANNEL_PINS_ON_GPIOC (CH1_PIN | CH2_PIN)

#define CONTROL_MODE_FREQ 0b0101
#define CONTROL_MODE_DUTY 0b1010

#define PWM_PERIOD 1000

#define I2C_RX_ADDR (0x17<<1) // the real address is still 0x17 because of internal shifting - i.e. master still sends to slave on 0x17

void IIC_Init(u32 bound, u16 address){
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
    RCC_APB1PeriphResetCmd(RCC_APB1Periph_I2C1, ENABLE);
    RCC_APB1PeriphResetCmd(RCC_APB1Periph_I2C1, DISABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);
    
    GPIO_InitTypeDef GPIO_InitStructure={0};
    GPIO_InitStructure.GPIO_Pin = SDA_PIN | SCL_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOC, &GPIO_InitStructure);

    I2C_InitTypeDef I2C_InitTSturcture={0};
    I2C_InitTSturcture.I2C_ClockSpeed = bound;
    I2C_InitTSturcture.I2C_Mode = I2C_Mode_I2C;
    I2C_InitTSturcture.I2C_DutyCycle = I2C_DutyCycle_16_9;
    I2C_InitTSturcture.I2C_OwnAddress1 = address;
    I2C_InitTSturcture.I2C_Ack = I2C_Ack_Enable;
    I2C_InitTSturcture.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
    I2C_Init(I2C1, &I2C_InitTSturcture);

    I2C_Cmd(I2C1, ENABLE);
}

void PWM_Init() {
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD | RCC_APB2Periph_GPIOC | RCC_APB2Periph_TIM1 | RCC_APB2Periph_AFIO, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    
    GPIO_PinRemapConfig(GPIO_PartialRemap1_TIM1, ENABLE);
    GPIO_PinRemapConfig(GPIO_FullRemap_TIM2, ENABLE);

    GPIO_InitTypeDef GPIO_InitStructure = {0};
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_InitStructure.GPIO_Pin = CHANNEL_PINS_ON_GPIOC;
    GPIO_Init(GPIOC, &GPIO_InitStructure);
    GPIO_InitStructure.GPIO_Pin = CHANNEL_PINS_ON_GPIOD;
    GPIO_Init(GPIOD, &GPIO_InitStructure);

    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure={0};
    TIM_TimeBaseInitStructure.TIM_Period = PWM_PERIOD;
    TIM_TimeBaseInitStructure.TIM_Prescaler = 0;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM1, &TIM_TimeBaseInitStructure);
    TIM_TimeBaseInit(TIM2, &TIM_TimeBaseInitStructure);

    TIM_OCInitTypeDef TIM_OCInitStructure={0};
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1; // Edge aligned
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0; // Start with 0% duty cycle
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;

    TIM_OC1Init(TIM1, &TIM_OCInitStructure);
    TIM_OC2Init(TIM1, &TIM_OCInitStructure);
    TIM_OC3Init(TIM2, &TIM_OCInitStructure);
    TIM_OC4Init(TIM2, &TIM_OCInitStructure);

    TIM_OC1PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC2PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC3PreloadConfig(TIM2, TIM_OCPreload_Enable);
    TIM_OC4PreloadConfig(TIM2, TIM_OCPreload_Enable);

    TIM_ARRPreloadConfig(TIM1, ENABLE);
    TIM_ARRPreloadConfig(TIM2, ENABLE);
    TIM_CtrlPWMOutputs(TIM1, ENABLE);
    //TIM_CtrlPWMOutputs(TIM2, ENABLE); // Not needed for TIM2
    TIM_Cmd(TIM1, ENABLE);
    TIM_Cmd(TIM2, ENABLE);
}

void PWM_UpdateDuty(uint8_t channel, uint16_t duty_cycle) {
    if (duty_cycle > PWM_PERIOD) {
        duty_cycle = PWM_PERIOD;
    }

    switch (channel) {
        case 1:
            TIM_SetCompare1(TIM1, duty_cycle);
            break;
        case 2:
            TIM_SetCompare2(TIM1, duty_cycle);
            break;
        case 3:
            TIM_SetCompare3(TIM2, duty_cycle);
            break;
        case 4:
            TIM_SetCompare4(TIM2, duty_cycle);
            break;
    }
}

void PWM_UpdatePeriod(uint8_t channel, uint16_t period, uint16_t prescaler) {
    switch (channel) {
        case 1:
        case 2:
            TIM1->PSC = prescaler;
            TIM1->ATRLR = period;
            TIM1->SWEVGR = TIM_PSCReloadMode_Immediate;
            break;
        case 3:
        case 4:
            TIM2->PSC = prescaler;
            TIM2->ATRLR = period;
            TIM2->SWEVGR = TIM_PSCReloadMode_Immediate;
            break;
    }
}

void PWM_UpdateFreq(uint8_t channel, uint16_t frequency) {
    // Since SystemCoreClock is usually no more than 48MHz and PWM_PERIOD is equal to 1000, 
    // the max effective PWM frequency is 48000Hz. Trying to set the frequency to anything 
    // greater than this value will cap the value to 48000Hz.
    uint32_t prescaler = SystemCoreClock / (PWM_PERIOD * frequency);
    if(prescaler == 0) {
        prescaler = 1;
    }

    PWM_UpdatePeriod(channel, PWM_PERIOD, (uint16_t)(prescaler) - 1);
}

int main(void) {
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();

    Delay_Ms(5);

    PWM_Init();
    IIC_Init(100000, I2C_RX_ADDR);
    I2C1->CTLR1 |= 0x0080; // CTLR1_NOSTRETCH_Set - Disable clock stretching
    I2C1->CTLR1 |= 0x0400; // CTLR1_ACK_Set - Enable ACK following each byte received - This also stops the clock stretching for each character received.
    // Thanks to Jim Merkle's code for those two lines above ^^: https://github.com/JimMerkle/CH32V003_I2C_Slave/blob/master/User/main.c
    // TODO: Try to get rid of those lines because they theoretically shouldn't be necassary but they are needed for I2C to work properly on my board. 

    Delay_Ms(5);

    uint8_t control_mode = 0;
    uint8_t target_channel = 0;
    uint8_t value_nth_byte = 0;
    uint16_t read_value = 0;

    volatile uint16_t temp;
    (void)temp;

    while (1) {
        while(!I2C_CheckEvent(I2C1, I2C_EVENT_SLAVE_RECEIVER_ADDRESS_MATCHED));

        // Clear ADDR
        temp = I2C1->STAR1;
        temp = I2C1->STAR2;

        /// Possible control options:
        // - Set PWM frequency per timer (two channels together)
        // - Set PWM duty cycle per channel.
        /// Setting duty cycle to 0 is equal to disabling the channel. All channels start at 0 by default.

        /// Motor control I2C packet:
        // - 1st byte (register) is composed of high nibble representing the channel (1, 2, 3 or 4) and a low nibble represeting the control mode (CONTROL_MODE_FREQ or CONTROL_MODE_DUTY)
        // - 2nd byte is the low byte of the 16 bit value
        // - 3rd byte is the high byte of the 16 bit value

        /// Take a look at pwm_board.py in the car's software to see the other side of the communication.

        /// The 16 bit value is:
        // - the PWM frequency in Hz if control mode is CONTROL_MODE_FREQ
        // - the PWM duty cycle that falls in the range [0; PWM_PERIOD] if control mode is CONTROL_MODE_DUTY

        // Receive bytes until STOP
        while (I2C_GetFlagStatus(I2C1, I2C_FLAG_STOPF) == RESET) {
            if (I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) != RESET) {
                uint8_t data = I2C_ReceiveData(I2C1);

                if (((data & 0b1111) == CONTROL_MODE_DUTY || (data & 0b1111) == CONTROL_MODE_FREQ) && control_mode == 0) {
                    control_mode = (data & 0b1111);
                    target_channel = ((data >> 4) & 0b1111);
                } else {
                    read_value |= ((uint16_t)data << (8 * value_nth_byte));
                    value_nth_byte++;
                }
            }
        }

        // Clear STOPF
        temp = I2C1->STAR1;
        I2C1->CTLR1 |= 0x0001;

        // Finish transfer and apply the read data
        if(value_nth_byte == 2 && control_mode != 0) {
            switch (control_mode) {
                case CONTROL_MODE_DUTY:
                    PWM_UpdateDuty(target_channel, read_value);
                    break;
                case CONTROL_MODE_FREQ:
                    PWM_UpdateFreq(target_channel, read_value);
                    break;
            }

            control_mode = 0;
            read_value = 0;
            value_nth_byte = 0;
        }
    }
}
