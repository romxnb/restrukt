<?php

namespace App\Security;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;
use Symfony\Component\Security\Core\Exception\CustomUserMessageAuthenticationException;
use Symfony\Component\Security\Http\Authenticator\AbstractAuthenticator;
use Symfony\Component\Security\Http\Authenticator\Passport\Badge\UserBadge;
use Symfony\Component\Security\Http\Authenticator\Passport\Passport;
use Symfony\Component\Security\Http\Authenticator\Passport\SelfValidatingPassport;
use Symfony\Component\Security\Http\EntryPoint\AuthenticationEntryPointInterface;

/**
 * Demo sign-in: the client names the employee in the X-Employee-Id header.
 */
class EmployeeHeaderAuthenticator extends AbstractAuthenticator implements AuthenticationEntryPointInterface
{
    private const HEADER = 'X-Employee-Id';

    public function supports(Request $request): bool
    {
        return $request->headers->has(self::HEADER);
    }

    public function authenticate(Request $request): Passport
    {
        $employeeId = (string) $request->headers->get(self::HEADER);
        if (!ctype_digit($employeeId)) {
            throw new CustomUserMessageAuthenticationException('Невідомий працівник.');
        }

        return new SelfValidatingPassport(new UserBadge($employeeId));
    }

    public function onAuthenticationSuccess(Request $request, TokenInterface $token, string $firewallName): ?Response
    {
        return null;
    }

    public function onAuthenticationFailure(Request $request, AuthenticationException $exception): Response
    {
        return new JsonResponse(['error' => 'Невідомий працівник.'], Response::HTTP_UNAUTHORIZED);
    }

    public function start(Request $request, ?AuthenticationException $authException = null): Response
    {
        return new JsonResponse(['error' => 'Потрібна автентифікація.'], Response::HTTP_UNAUTHORIZED);
    }
}
