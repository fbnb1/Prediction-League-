package com.predictionleague.ledger.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.ExchangeBuilder;
import org.springframework.amqp.core.FanoutExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * RabbitMQ topology for the Ledger service. The exchange/queue names match
 * docs/event-contracts.md. Declared idempotently on startup by RabbitAdmin.
 */
@Configuration
public class RabbitConfig {

    public static final String EVENTS_EXCHANGE = "prediction-league.events";
    public static final String DEAD_LETTER_EXCHANGE = "prediction-league.dlx";
    public static final String MATCH_SETTLED_QUEUE = "ledger.match-settled";
    public static final String MATCH_SETTLED_DLQ = "ledger.match-settled.dlq";
    public static final String MATCH_SETTLED_ROUTING_KEY = "match.settled";

    @Bean
    TopicExchange eventsExchange() {
        return ExchangeBuilder.topicExchange(EVENTS_EXCHANGE).durable(true).build();
    }

    @Bean
    FanoutExchange deadLetterExchange() {
        return ExchangeBuilder.fanoutExchange(DEAD_LETTER_EXCHANGE).durable(true).build();
    }

    @Bean
    Queue matchSettledQueue() {
        return QueueBuilder.durable(MATCH_SETTLED_QUEUE)
                .withArgument("x-dead-letter-exchange", DEAD_LETTER_EXCHANGE)
                .build();
    }

    @Bean
    Queue matchSettledDlq() {
        return QueueBuilder.durable(MATCH_SETTLED_DLQ).build();
    }

    @Bean
    Binding matchSettledBinding() {
        return BindingBuilder.bind(matchSettledQueue()).to(eventsExchange()).with(MATCH_SETTLED_ROUTING_KEY);
    }

    @Bean
    Binding matchSettledDlqBinding() {
        return BindingBuilder.bind(matchSettledDlq()).to(deadLetterExchange());
    }

    @Bean
    MessageConverter jsonMessageConverter(ObjectMapper objectMapper) {
        return new Jackson2JsonMessageConverter(objectMapper);
    }
}
