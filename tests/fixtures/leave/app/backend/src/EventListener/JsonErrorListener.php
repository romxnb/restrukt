<?php

namespace App\EventListener;

use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;
use Symfony\Component\Validator\Exception\ValidationFailedException;

/**
 * API errors reach the client as {"error": "<message for the user>"}.
 *
 * Runs after Symfony has turned exceptions mapped in framework.exceptions or marked with #[WithHttpStatus] into HTTP ones.
 */
#[AsEventListener(priority: -64)]
final class JsonErrorListener
{
    public function __invoke(ExceptionEvent $event): void
    {
        if (!str_starts_with($event->getRequest()->getPathInfo(), '/api/')) {
            return;
        }

        $exception = $event->getThrowable();
        if (!$exception instanceof HttpExceptionInterface) {
            return;
        }

        $message = $exception->getMessage();
        $previous = $exception->getPrevious();
        if ($previous instanceof ValidationFailedException && \count($previous->getViolations()) > 0) {
            $message = (string) $previous->getViolations()->get(0)->getMessage();
        }

        $event->setResponse(new JsonResponse(['error' => $message], $exception->getStatusCode(), $exception->getHeaders()));
    }
}
