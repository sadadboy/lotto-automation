# src/domain/entities/recharge_settings.py
from dataclasses import dataclass


@dataclass
class RechargeSettings:
    """자동충전 설정 엔티티"""
    
    auto_recharge: bool
    minimum_balance: int  # 최소 잔액 (원)
    recharge_amount: int  # 충전 금액 (원)
    
    def __post_init__(self):
        """생성 후 검증"""
        self._validate()
    
    def _validate(self):
        """자동충전 설정 검증"""
        if not isinstance(self.auto_recharge, bool):
            raise ValueError("auto_recharge는 boolean 타입이어야 합니다.")
        
        if not isinstance(self.minimum_balance, int) or self.minimum_balance < 0:
            raise ValueError("최소 잔액은 0 이상의 정수여야 합니다.")
        
        if not isinstance(self.recharge_amount, int) or self.recharge_amount < 1000:
            raise ValueError("충전 금액은 1,000원 이상이어야 합니다.")
        
        # 최소 잔액이 충전 금액보다 크면 안됨
        if self.minimum_balance >= self.recharge_amount:
            raise ValueError("최소 잔액이 충전 금액보다 작아야 합니다.")
        
        # 충전 금액은 1,000원 단위여야 함
        if self.recharge_amount % 1000 != 0:
            raise ValueError("충전 금액은 1,000원 단위여야 합니다.")
    
    def is_valid(self) -> bool:
        """설정이 유효한지 확인"""
        try:
            self._validate()
            return True
        except ValueError:
            return False
    
    def should_recharge(self, current_balance: int) -> bool:
        """충전이 필요한지 확인"""
        if not self.auto_recharge:
            return False
        
        return current_balance < self.minimum_balance
    
    def get_recharge_amount(self, current_balance: int) -> int:
        """충전할 금액 반환"""
        if not self.should_recharge(current_balance):
            return 0
        
        return self.recharge_amount
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "auto_recharge": self.auto_recharge,
            "minimum_balance": self.minimum_balance,
            "recharge_amount": self.recharge_amount
        }
    
    @classmethod
    def default(cls) -> 'RechargeSettings':
        """기본 설정 반환"""
        return cls(
            auto_recharge=True,
            minimum_balance=5000,
            recharge_amount=50000
        )
