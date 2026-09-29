<?php

namespace App\Controller;

use App\Dto\ProfileUpdate;
use App\Entity\Employee;
use App\Repository\EmployeeRepository;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\CurrentUser;

#[Route('/api')]
final class EmployeeController extends AbstractController
{
    /**
     * Employees to choose from on the demo sign-in page.
     */
    #[Route('/employees', methods: ['GET'])]
    public function list(EmployeeRepository $employees): JsonResponse
    {
        return $this->json(array_map(
            static fn (Employee $employee) => ['id' => $employee->getId(), 'name' => $employee->getName()],
            $employees->findAllOrderedByName(),
        ));
    }

    #[Route('/me', methods: ['GET'])]
    public function me(#[CurrentUser] Employee $me): JsonResponse
    {
        return $this->json($this->profile($me));
    }

    #[Route('/me', methods: ['PATCH'])]
    public function updateProfile(
        #[CurrentUser] Employee $me,
        #[MapRequestPayload] ProfileUpdate $update,
        EntityManagerInterface $entityManager,
    ): JsonResponse {
        $me->rename(trim($update->name));
        $entityManager->flush();

        return $this->json($this->profile($me));
    }

    #[Route('/team/members', methods: ['GET'])]
    public function teamMembers(#[CurrentUser] Employee $me, EmployeeRepository $employees): JsonResponse
    {
        return $this->json(array_map(
            static fn (Employee $member) => [
                'id' => $member->getId(),
                'name' => $member->getName(),
                'email' => $member->getEmail(),
                'isManager' => $member->isManager(),
            ],
            $employees->findTeamMembers($me->getTeam()),
        ));
    }

    /**
     * @return array<string, mixed>
     */
    private function profile(Employee $employee): array
    {
        return [
            'id' => $employee->getId(),
            'name' => $employee->getName(),
            'email' => $employee->getEmail(),
            'team' => ['id' => $employee->getTeam()->getId(), 'name' => $employee->getTeam()->getName()],
            'isManager' => $employee->isManager(),
        ];
    }
}
