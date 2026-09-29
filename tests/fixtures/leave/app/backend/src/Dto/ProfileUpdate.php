<?php

namespace App\Dto;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class ProfileUpdate
{
    public function __construct(
        #[Assert\NotBlank(message: 'Вкажіть ім\'я.')]
        #[Assert\Length(max: 100, maxMessage: 'Ім\'я не довше за {{ limit }} символів.')]
        public string $name = '',
    ) {
    }
}
