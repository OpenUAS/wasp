#ifndef COMM_H
#define COMM_H

//#include "std.h"
#include "generated/messages.h"

typedef enum {
    COMM_1,
    COMM_2,
    COMM_NB
} CommChannel_t;

typedef enum {
    STATE_UNINIT,
    STATE_GOT_STX,
    STATE_GOT_LENGTH,
    STATE_GOT_ACID,
    STATE_GOT_MSGID,
    STATE_GOT_PAYLOAD,
    STATE_GOT_CRC1
} ParseState_t; ///< The state machine for the comm parser
    
typedef struct __CommStatus {
    uint8_t ck_a; ///< Checksum byte 1
    uint8_t ck_b; ///< Checksum byte 2
    uint8_t msg_received;
    uint8_t buffer_overrun; ///< Number of buffer overruns
    uint8_t parse_error; ///< Number of parse errors
    ParseState_t parse_state; ///< Parsing state machine
} CommStatus_t;

typedef uint8_t (*CommMessageCallback_t)(CommMessage_t *message);

extern CommMessageCallback_t    comm_callback[COMM_NB];
extern CommMessage_t            comm_message[COMM_NB];
extern CommStatus_t             comm_status[COMM_NB];
extern uint8_t                  comm_channel_used[COMM_NB];

/**
 * @brief Initialize the communication channel
 */
void comm_init ( CommChannel_t chan );

void
comm_periodic_task ( CommChannel_t chan );

uint8_t
comm_event_task ( CommChannel_t chan );

uint8_t
comm_ch_available ( CommChannel_t chan );

/**
 * @brief Send one char over the comm channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan the comm channel
 * @param c char to send
 */
void comm_send_ch ( CommChannel_t chan, uint8_t c );

/**
 * @brief Send a whole message over a the comm channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan the comm channel
 * @param message the message to send
 */
void comm_send_message ( CommChannel_t chan, CommMessage_t* message );

uint8_t
comm_send_message_by_id (CommChannel_t chan, uint8_t msgid);

/**
 * @brief Get one char from the comm channel
 *
 * This stub has to be implemented by each individual platform
 *
 * @param chan The channel to get one char from
 * @return The next char
 */
uint8_t comm_get_ch( CommChannel_t chan );

uint8_t
comm_check_free_space ( CommChannel_t chan, uint8_t len );

void
comm_start_message ( CommChannel_t chan, uint8_t id, uint8_t len );

void
comm_end_message ( CommChannel_t chan );

uint8_t
comm_parse ( CommChannel_t chan );

#endif /* COMM_H */

